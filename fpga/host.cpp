#include "host.h"
#include "json.hpp"
#include "spdlog/spdlog.h"
#include <CL/opencl.hpp>
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
  using std::filesystem::path;
  using spdlog::info;

  if (argc != 4) {
    usage(argv[0]);
    return EXIT_FAILURE;
  }

  cl::Context context;
  cl::Platform platform;
  cl::Device device;

  cl_int err;
  get_first_device(context, platform, device);

  // Using an out-of-order queue, so we can have true parallelism
  cl::CommandQueue queue(
      context, device,
      CL_QUEUE_PROFILING_ENABLE | CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE, &err);

  path graph_path(argv[1]);
  path xlbin_path(argv[2]);
  path schedule_path(argv[3]);

  cl::Program::Binaries bins;
  read_binaries(xlbin_path, bins);
  cl::Program program(context, {device}, bins, nullptr, &err);

  Graph graph;
  boost::dynamic_properties properties(boost::ignore_other_properties);
  read_graph(graph_path, graph, properties);
  assert(num_vertices(graph) > 0);

  Schedule schedule;
  read_schedule(schedule_path, graph, schedule);
  assert(schedule.size() == num_vertices(graph));

  Machine machine;
  read_machine_model(schedule_path, machine);
}

cl_int get_kernel_cost(const ScheduledTask& task) {
  // TODO: project this to actual hardware numbers
  return task.cost[task.pe.id];
}

void execute_dag_with_schedule(cl::Context &context, cl::Program &program,
                               const Graph &graph, const Schedule &schedule) {
  cl_int err;
  aligned_vector<cl::Event> events;

  // Mutable copy
  Schedule sorted_schedule = schedule;
  std::sort(sorted_schedule.begin(), sorted_schedule.end(),
            [](const auto &lhs, const auto &rhs) { return lhs.t_s < rhs.t_s; });

  for (auto &task : sorted_schedule) {
    // enqueue...
  }
}
