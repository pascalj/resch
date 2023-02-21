#include "spdlog/spdlog.h"
#include <algorithm>
#include <cstdio>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#define CL_HPP_TARGET_OPENCL_VERSION 200
#include <CL/opencl.hpp>
#include <boost/align/aligned_allocator.hpp>
#include <boost/graph/directed_graph.hpp>
#include <boost/graph/graphml.hpp>

using std::filesystem::path;

// Use a page-aligned vector
template <typename T>
using aligned_vector =
    std::vector<T, boost::alignment::aligned_allocator<T, 4096>>;

using spdlog::info;

size_t offset = 0;
size_t global = 1;
size_t local = 1;

// An event callback function that prints the operations performed by the OpenCL
// runtime.

void event_cb(cl_event event1, cl_int cmd_status, void *data) {
  cl_int err;
  cl_command_type command;
  cl::Event event(event1, true);
  event.getInfo<cl_command_type>(CL_EVENT_COMMAND_TYPE, &command);
  cl_int status;
  event.getInfo<cl_int>(CL_EVENT_COMMAND_EXECUTION_STATUS, &status);

  const char *command_str;
  const char *status_str;
  switch (command) {
  case CL_COMMAND_READ_BUFFER:
    command_str = "buffer read";
    break;
  case CL_COMMAND_WRITE_BUFFER:
    command_str = "buffer write";
    break;
  case CL_COMMAND_NDRANGE_KERNEL:
    command_str = "kernel";
    break;
  }
  switch (status) {
  case CL_QUEUED:
    status_str = "Queued";
    break;
  case CL_SUBMITTED:
    status_str = "Submitted";
    break;
  case CL_RUNNING:
    status_str = "Executing";
    break;
  case CL_COMPLETE:
    status_str = "Completed";
    break;
  }
  printf("%s %s %s\n", status_str, reinterpret_cast<char *>(data), command_str);
  fflush(stdout);
}

// Sets the callback for a particular event
void set_callback(cl::Event event, const char *queue_name) {
  cl_int err;
  event.setCallback(CL_COMPLETE, event_cb, (void *)queue_name);
}

void execute_dag(cl::Context &context, cl::Device &device) {
  cl_int err;
  aligned_vector<cl::Event> ooo_events;
  aligned_vector<cl::Event> kernel_wait_events;
  cl::CommandQueue ooo_queue(
      context, device,
      CL_QUEUE_PROFILING_ENABLE | CL_QUEUE_OUT_OF_ORDER_EXEC_MODE_ENABLE, &err);

  const int matrix_scale_factor = 2;
}

void get_first_device(cl::Context &context, cl::Platform &platform,
                      cl::Device &device) {
  std::vector<cl::Platform> platforms;
  cl::Platform::get(&platforms);
  info("Found {} platforms:", platforms.size());
  for (auto &platform : platforms) {
    info("\t{}", platform.getInfo<CL_PLATFORM_NAME>());
  }
  assert(platforms.size() == 1);

  // cheap to copy
  platform = platforms[0];
  info("Selected {}", platform.getInfo<CL_PLATFORM_NAME>());

  std::vector<cl::Device> devices;
  platform.getDevices(CL_DEVICE_TYPE_ALL, &devices);
  info("Found {} devices:", devices.size());
  for (auto &device : devices) {
    info("\t{}", device.getInfo<CL_DEVICE_NAME>());
  }
  assert(platforms.size() >= 1);

  device = devices[0];
  info("Selected {}", device.getInfo<CL_DEVICE_NAME>());

  cl::Context device_ctx(device);
  context = device_ctx;
}

void read_binaries(const path directory, cl::Program::Binaries out,
                   const std::string &extension = ".xclbin") {
  for (auto entry : std::filesystem::directory_iterator{directory}) {
    if (entry.is_regular_file() && entry.path().extension() == extension) {
      std::ifstream is(entry.path());
      std::istream_iterator<unsigned char> start(is), end;
      std::vector<unsigned char> binary(start, end);
      out.push_back(std::move(binary));
      info("Read {} bytes from {}", out.back().size(),
           entry.path().filename().c_str());
    }
  }
  info("Read {} binaries from {}", out.size(), directory.c_str());
}

void read_graph(const path &graph_path, boost::directed_graph<> &graph,
                boost::dynamic_properties &properties) {
  std::ifstream is(graph_path);
  boost::read_graphml(is, graph, properties);
  info("Imported {} with {} vertices and {} edges",
       graph_path.filename().c_str(), graph.num_vertices(), graph.num_edges());
}

int main(int argc, char **argv) {
  if (argc != 3) {
    std::cout << "Usage: " << argv[0] << " <Graph.xml> <configuration.xclbin>"
              << std::endl;
    return EXIT_FAILURE;
  }

  cl::Context context;
  cl::Platform platform;
  cl::Device device;

  std::filesystem::path graph_path(argv[1]);
  std::filesystem::path xlbin_path(argv[2]);
  cl::Program::Binaries bins;
  read_binaries(xlbin_path, bins);

  boost::directed_graph<> graph;
  boost::dynamic_properties properties(boost::ignore_other_properties);
  read_graph(graph_path, graph, properties);

  cl_int err;
  get_first_device(context, platform, device);
  cl::Program program(context, {device}, bins, nullptr, &err);
}
