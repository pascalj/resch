#include "host.h"
#include "json.hpp"
#include "spdlog/spdlog.h"
#include <CL/cl2.hpp>
#include <algorithm>
#include <boost/graph/directed_graph.hpp>
#include <boost/graph/graphml.hpp>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

/**
 * @brief Execute task graphs using OpenCL
 *
 * Parse a task graph from GraphML and a schedule from a csv file and
 * execute the schedules' task using a set of provided configurations.
 *
 */
int main(int argc, char **argv) {
  using spdlog::info;
  using std::filesystem::path;
  spdlog::set_level(spdlog::level::debug);

  if (argc != 4) {
    usage(argv[0]);
    return EXIT_FAILURE;
  }

  // Paths/arguments
  path graph_path(argv[1]);
  path xlbin_path(argv[2]);
  path schedule_path(argv[3]);

  // Static CL variables
  cl::Context context;
  cl::Platform platform;
  cl::Device device;
  get_first_device(context, platform, device);

  // Load and initialize graph, schedule and machine model
  Graph graph;
  boost::dynamic_properties properties(boost::ignore_other_properties);
  read_graph(graph_path, graph, properties);

  Schedule schedule;
  read_schedule(schedule_path, graph, schedule);

  Machine machine;
  read_machine_model(schedule_path, machine);
  machine.init(context, device, xlbin_path);

  cl::Buffer out_buf(context, CL_MEM_READ_WRITE, sizeof(int));
  cl::Buffer in_buf(context, CL_MEM_READ_WRITE, sizeof(int) * (1 << max_bufsize_shift));
  tune_parameters(context, device, machine.configs[0],
                  [&out_buf, &in_buf](int i, cl::Kernel &kernel) {
                    int size = 1 << i;
                    kernel.setArg(0, size);
                    kernel.setArg(1, in_buf);
                    kernel.setArg(2, 0);
                    kernel.setArg(3, out_buf);
                  });
  tune_parameters(context, device, machine.configs[0],
                  [&out_buf, &in_buf](int i, cl::Kernel &kernel) {
                    int size = 1 << i;
                    kernel.setArg(0, 1);
                    kernel.setArg(1, in_buf);
                    kernel.setArg(2, size);
                    kernel.setArg(3, out_buf);
                  });

  // Finally, execute the graph
  execute_dag_with_allocation(context, machine, graph, schedule);
}

cl_int get_kernel_cost(const ScheduledTask &task) {
  // TODO: project this to actual hardware numbers
  return task.cost[task.pe_id];
}

std::pair<int, int>
tune_parameters(const cl::Context &ctx, const cl::Device &dev,
                Configuration &conf,
                std::function<void(int, cl::Kernel &)> set_args) {
  auto queue = cl::CommandQueue(ctx, dev, CL_QUEUE_PROFILING_ENABLE);
  std::vector<cl::Event> events;

  cl::NDRange gsize(1);
  cl::NDRange offset(0);
  cl::NDRange lsize(1);

  // Execute a range of kernels and double the "compute size" every time. Also
  // track the timing (CL_QUEUE_PROFILING_ENABLE) and save it into
  // 'measurements'.
  for (int i = 1; i < max_bufsize_shift; i++) {
    auto &pe = conf.PEs.front();
    set_args(i, pe.kernel);
    auto &event = events.emplace_back();
    queue.enqueueNDRangeKernel(pe.kernel, offset, gsize, lsize, nullptr,
                               &event);
  }
  queue.flush();
  queue.finish();

  cl::vector<std::pair<int, int>> measurements;
  int i = 1;
  for (auto &event : events) {
    auto start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
    auto end = event.getProfilingInfo<CL_PROFILING_COMMAND_COMPLETE>();
    measurements.emplace_back(i, end - start);
    i = i << 1;
  }

  return linreg(measurements);
}

std::pair<int, int> linreg(const std::vector<Measurement>& measurements) {
  // Simple linear regression
  auto avg_x =
      std::accumulate(measurements.begin(), measurements.end(), 0.,
                      [](auto acc, auto point) { return acc + point.first; }) /
      measurements.size();
  auto avg_y =
      std::accumulate(measurements.begin(), measurements.end(), 0.,
                      [](auto acc, auto point) { return acc + point.second; }) /
      measurements.size();
  auto numerator = std::accumulate(
      measurements.begin(), measurements.end(), 0., [=](auto acc, auto point) {
        return (point.first - avg_x) * (point.second - avg_y);
      });
  auto denominator = std::accumulate(
      measurements.begin(), measurements.end(), 0., [=](auto acc, auto point) {
        return (point.first - avg_x) * (point.first - avg_x);
      });

  auto beta_1 = numerator / denominator;
  auto beta_0 = avg_y - beta_1 * avg_x;

  // Check coefficient of determination R^2.
  // We should be able to get a value very near 1.
  auto sqr = std::accumulate(
      measurements.begin(), measurements.end(), 0., [=](auto acc, auto point) {
        auto y_hat = beta_0 + beta_1 * point.first;
        return (point.second - y_hat) * (point.second - y_hat);
      });
  auto sqt = std::accumulate(
      measurements.begin(), measurements.end(), 0., [=](auto acc, auto point) {
        return (point.second - avg_y) * (point.second - avg_y);
      });
  auto R_squared = 1. - (sqr / sqt);
  spdlog::debug("beta_0: {}, beta_1: {} (R^2: {})", beta_0, beta_1, R_squared);
  assert(R_squared > 0.9 && R_squared <= 1);

  return std::make_pair(beta_0, beta_1);
}

void execute_dag_with_allocation(cl::Context &context, const Machine &machine,
                                 const Graph &graph, const Schedule &schedule) {
  cl_int err;

  std::map<uint32_t, cl::Event> events;

  // Using an out-of-order queue, so we can have true parallelism
  cl::CommandQueue queue(
      context, machine.device,
      CL_QUEUE_PROFILING_ENABLE | CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE, &err);

  // Mutable copy
  Schedule sorted_schedule = schedule;
  std::sort(sorted_schedule.begin(), sorted_schedule.end(),
            [](const auto &lhs, const auto &rhs) { return lhs.t_s < rhs.t_s; });

  // This is topologically sorted, so we can just enqueue these as-is
  for (auto &task : sorted_schedule) {
    cl::Event task_event;
    auto& pe = machine.pe(task.pe_id);
    events.insert(std::make_pair(task.id, task_event));
    std::cout << "task id: " << task.id << std::endl;
    auto edge_its = in_edges(task.id, graph);
    std::vector<cl::Event> dependent;
    std::for_each(edge_its.first, edge_its.second, [&] (auto it) {
      auto stask = source(it, graph);
      assert(events.count(stask) == 1);
      dependent.push_back(events[stask]);
    });
    err = queue.enqueueNDRangeKernel(pe.kernel, 0, 0, cl::NullRange, &dependent, &events[task.id]);
    spdlog::debug("Enqueued task {}: {}", task.label, err == CL_SUCCESS);
  }

  queue.flush();
  queue.finish();

  for(auto &event_pair : events) {
    auto event = event_pair.second;

    auto start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
    auto end = event.getProfilingInfo<CL_PROFILING_COMMAND_COMPLETE>();

    spdlog::info("Task {}: [{}, {})", event_pair.first, start, end);
  }
}
