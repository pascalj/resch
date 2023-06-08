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

using namespace std::literals::chrono_literals;

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
  cl::Platform platform;
  cl::Device device;
  get_first_device(platform, device);
  cl_int err;
  auto context = cl::Context(device, nullptr, nullptr, nullptr, &err);

  // Load and initialize graph, schedule and machine model
  Graph graph;
  boost::dynamic_properties properties(boost::ignore_other_properties);
  read_graph(graph_path, graph, properties);

  Schedule schedule;
  read_schedule(schedule_path, graph, schedule);

  Machine machine;
  read_machine_model(schedule_path, machine);
  machine.init(context, device, xlbin_path);

  Parameters params;
  params.init(context, device, machine.configs[0]);

  // Finally, execute the graph
  execute_dag_with_allocation(context, machine, graph, schedule, params);
}

cl_int get_kernel_cost(const ScheduledTask &task) {
  // TODO: project this to actual hardware numbers
  return task.cost[task.pe_id];
}

std::pair<int, int>
Parameters::tune_parameters(const cl::Context &ctx, const cl::Device &dev,
                Configuration &conf,
                std::function<void(int, cl::Kernel &)> set_args) {
  auto queue = cl::CommandQueue(ctx, CL_QUEUE_PROFILING_ENABLE);
  std::vector<cl::Event> events;

  cl::NDRange gsize(1);
  cl::NDRange offset(0);
  cl::NDRange lsize(1);

  // Execute a range of kernels and double the "compute size" every time. Also
  // track the timing (CL_QUEUE_PROFILING_ENABLE) and save it into
  // 'measurements'.
  for (int i = 1; i < 5; i++) {
    auto &pe = conf.PEs.front();
    set_args(1, pe.kernel);
    queue.enqueueNDRangeKernel(pe.kernel, offset, gsize, lsize, nullptr,
                               nullptr);
  }
  for (int i = 1; i < max_compsize_shift; i++) {
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
    i = i << 1;
    auto start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
    auto end = event.getProfilingInfo<CL_PROFILING_COMMAND_END>();
    spdlog::debug("Kernel event:{}:{}", i, end-start);
    measurements.emplace_back(i, end - start);
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

void execute_dag_with_allocation(cl::Context &context, Machine &machine,
                                 const Graph &graph, const Schedule &schedule, const Parameters& param) {
  cl_int err;

  std::map<uint32_t, cl::Event> events;

  // Using an out-of-order queue, so we can have true parallelism
  cl::CommandQueue queue(
      context, machine.device,
      CL_QUEUE_PROFILING_ENABLE | CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE, &err);
  cl::Buffer out_buf(context, CL_MEM_READ_WRITE, sizeof(int));
  cl::Buffer in_buf(context, CL_MEM_READ_WRITE, sizeof(int) * (1 << max_bufsize_shift));

  // Mutable copy
  Schedule sorted_schedule = schedule;
  std::sort(sorted_schedule.begin(), sorted_schedule.end(),
            [](const auto &lhs, const auto &rhs) { return lhs.t_s < rhs.t_s; });

  // This is topologically sorted, so we can just enqueue these as-is
  for (auto &task : sorted_schedule) {
    // Get the incomming edges and wait for the respective tasks' events
    cl::Event task_event;
    auto &pe = machine.pe(task.pe_id);
    events.insert(std::make_pair(task.id, task_event));
    auto edge_its = in_edges(task.id, graph);

    std::vector<cl::Event> dependent;
    std::for_each(edge_its.first, edge_its.second, [&](auto it) {
      auto src_task = source(it, graph);
      // A source task should have exactly one event attached
      assert(events.count(src_task) == 1);
      dependent.push_back(events[src_task]);
    });

    auto computation_cost =
        param.predict_compute_size(task.cost_as<std::chrono::milliseconds>());
    auto data_cost = param.predict_data_size(1ms);

    // Enqueue the task
    cl::NDRange gsize(1);
    cl::NDRange offset(0);
    cl::NDRange lsize(1);
    pe.kernel.setArg(0, computation_cost);
    pe.kernel.setArg(1, in_buf);
    pe.kernel.setArg(2, data_cost);
    pe.kernel.setArg(3, out_buf);
    err = queue.enqueueNDRangeKernel(pe.kernel, offset, gsize, lsize, &dependent,
                                     &events[task.id]);
    spdlog::debug("Enqueued task {}: {},", task.label, err == CL_SUCCESS);
  }

  queue.flush();
  queue.finish();

  for(auto &event_pair : events) {
    auto event = event_pair.second;

    auto start = event.getProfilingInfo<CL_PROFILING_COMMAND_START>();
    auto end = event.getProfilingInfo<CL_PROFILING_COMMAND_END>();
    std::chrono::nanoseconds duration(end - start);

    spdlog::info("Task {}: {}ms [{}, {})", event_pair.first, std::chrono::duration_cast<std::chrono::milliseconds>(duration).count(), start, end);
  }
}
