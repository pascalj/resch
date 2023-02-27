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

  // Finally, execute the graph
  execute_dag_with_allocation(context, machine, graph, schedule);
}

cl_int get_kernel_cost(const ScheduledTask &task) {
  // TODO: project this to actual hardware numbers
  return task.cost[task.pe_id];
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
    // enqueue...
    cl::Event task_event;
    // TODO...
    auto& pe = machine.pe(task.pe_id);
    events.insert(std::make_pair(task.id, task_event));
    std::cout << "task id: " << task.id << std::endl;
    auto edge_its = in_edges(task.id, graph);
    std::vector<cl::Event> dependent;
    std::for_each(edge_its.first, edge_its.second, [&] (auto it) {
      auto stask = source(it, graph);
      std::cout << "Indep: " << stask << std::endl;
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
