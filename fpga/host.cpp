#include "host.h"
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
#include <boost/graph/directed_graph.hpp>
#include <boost/graph/graphml.hpp>

using std::filesystem::path;

using spdlog::info;

void execute_dag(cl::Context &context, cl::Device &device) {
  cl_int err;
  aligned_vector<cl::Event> ooo_events;
  aligned_vector<cl::Event> kernel_wait_events;
  cl::CommandQueue queue(
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
      std::ifstream is(entry.path(), std::ios::binary);
      std::istream_iterator<unsigned char> start(is), end;
      std::vector<unsigned char> binary(start, end);
      out.push_back(std::move(binary));
      info("Read {} bytes from {}", out.back().size(),
           entry.path().filename().c_str());
    }
  }
  info("Read {} binaries from {}", out.size(), directory.c_str());
}

std::string vec2str(std::vector<int>) { return ""; }
auto str2vec(std::string const &str) -> std::vector<int> {
  auto number = 0;
  auto out = str;
  auto vec = std::vector<int>{};
  std::transform(str.cbegin(), str.cend(), out.begin(),
                 [](char ch) { return (ch == ',') ? ' ' : ch; });
  auto strs = std::stringstream{out};
  while (strs >> number) {
    vec.push_back(number);
  }
  return vec;
}

void read_graph(const path &graph_path, Graph &graph,
                boost::dynamic_properties &properties) {
  std::ifstream is(graph_path, std::ios::binary);
  properties.property("label", boost::get(&Task::label, graph));
  properties.property(
      "comm",
      TranslateStringPMap{boost::get(&Dependency::cost, graph), vec2str, str2vec});
  properties.property(
      "cost",
      TranslateStringPMap{boost::get(&Task::cost, graph), vec2str, str2vec});
  boost::read_graphml(is, graph, properties);
  info("Imported {} with {} vertices and {} edges",
       graph_path.filename().c_str(), boost::num_vertices(graph), boost::num_edges(graph));
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

  Graph graph;
  boost::dynamic_properties properties(boost::ignore_other_properties);
  read_graph(graph_path, graph, properties);

  cl_int err;
  get_first_device(context, platform, device);
  cl::Program program(context, {device}, bins, nullptr, &err);
}
