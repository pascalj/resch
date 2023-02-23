#pragma once

#include "boost/graph/graphml.hpp"
#include "boost/property_map/dynamic_property_map.hpp"
#define CL_HPP_TARGET_OPENCL_VERSION 200
#include "spdlog/spdlog.h"
#include <CL/opencl.hpp>
#include <boost/align/aligned_allocator.hpp>
#include <boost/graph/directed_graph.hpp>
#include <boost/property_map/property_map.hpp>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

struct Task {
  uint32_t id;
  std::string label;
  std::vector<int> cost;
};

struct ScheduledTask : Task {
  uint32_t t_s;
  uint32_t PE;
};

struct Dependency {
  std::vector<int> cost;
};

// Use a page-aligned vector
template <typename T>
using aligned_vector =
    std::vector<T, boost::alignment::aligned_allocator<T, 4096>>;

// A schedule is the set of ScheduledTasks, since they contain t_s and the PE
using Schedule = std::vector<ScheduledTask>;

/* using Graph = boost::directed_graph<Task, Dependency>; */
using Graph = boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS,
                                    Task, Dependency>;

// https://stackoverflow.com/questions/73309661/how-to-interpret-complex-strings-as-graph-properties-when-reading-a-graphml-file
template <typename PMap, typename ToString, typename FromString>
class TranslateStringPMap {
public:
  using category = boost::read_write_property_map_tag;
  using key_type = typename boost::property_traits<PMap>::key_type;
  using reference = std::string;
  using value_type = std::string;

  TranslateStringPMap(PMap wrapped_pmap, ToString to_string,
                      FromString from_string)
      : wrapped_pmap{wrapped_pmap}, to_string{to_string}, from_string{
                                                              from_string} {}

  auto friend get(TranslateStringPMap const &translator, key_type const &key)
      -> value_type {
    return translator.to_string(get(translator.wrapped_pmap, key));
  }

  auto friend put(TranslateStringPMap const &translator, key_type const &key,
                  value_type const &value) -> void {
    boost::put(translator.wrapped_pmap, key, translator.from_string(value));
  }

private:
  PMap wrapped_pmap;
  ToString to_string;
  FromString from_string;
};


inline void get_first_device(cl::Context &context, cl::Platform &platform,
                      cl::Device &device) {
  std::vector<cl::Platform> platforms;
  cl::Platform::get(&platforms);
  spdlog::info("Found {} platforms:", platforms.size());
  for (auto &platform : platforms) {
    spdlog::info("\t{}", platform.getInfo<CL_PLATFORM_NAME>());
  }
  assert(platforms.size() == 1);

  // cheap to copy
  platform = platforms[0];
  spdlog::info("Selected {}", platform.getInfo<CL_PLATFORM_NAME>());

  std::vector<cl::Device> devices;
  platform.getDevices(CL_DEVICE_TYPE_ALL, &devices);
  spdlog::info("Found {} devices:", devices.size());
  for (auto &device : devices) {
    spdlog::info("\t{}", device.getInfo<CL_DEVICE_NAME>());
  }
  assert(platforms.size() >= 1);

  device = devices[0];
  spdlog::info("Selected {}", device.getInfo<CL_DEVICE_NAME>());

  cl::Context device_ctx(device);
  context = device_ctx;
}

inline std::string vec2str(std::vector<int>);
inline auto str2vec(std::string const &str) -> std::vector<int>;
inline void read_graph(const std::filesystem::path &graph_path, Graph &graph,
                boost::dynamic_properties &properties) {
  std::ifstream is(graph_path, std::ios::binary);
  properties.property("label", boost::get(&Task::label, graph));
  properties.property("comm",
                      TranslateStringPMap{boost::get(&Dependency::cost, graph),
                                          vec2str, str2vec});
  properties.property(
      "cost",
      TranslateStringPMap{boost::get(&Task::cost, graph), vec2str, str2vec});
  boost::read_graphml(is, graph, properties);
  spdlog::info("Imported {} with {} vertices and {} edges",
       graph_path.filename().c_str(), boost::num_vertices(graph),
       boost::num_edges(graph));
}

inline void read_schedule_from_csv(const std::filesystem::path &schedule_path, Schedule &schedule) {
  std::ifstream is(schedule_path, std::ios::binary);
  std::vector<std::string> result;
  std::string line;

  while (std::getline(is, line)) {
    std::stringstream line_stream(line);
    std::string tok;
    ScheduledTask task;
    std::getline(line_stream, tok, ',');
    task.id = std::stoi(tok);
    std::getline(line_stream, tok, ',');
    task.t_s = std::stoi(tok);
    std::getline(line_stream, tok, ',');
    task.PE = std::stoi(tok);

    schedule.push_back(std::move(task));
  }
}


/**
 * @brief Execute the DAG found in graph on device using schedule
 *
 * @param context 
 * @param device 
 * @param graph 
 * @param schedule 
 */
void execute_dag_with_schedule(cl::Context &context, cl::Device &device, const Graph &graph,
                 const Schedule &schedule);

inline void read_binaries(const std::filesystem::path directory,
                          cl::Program::Binaries out,
                          const std::string &extension = ".xclbin") {
  for (auto entry : std::filesystem::directory_iterator{directory}) {
    if (entry.is_regular_file() && entry.path().extension() == extension) {
      std::ifstream is(entry.path(), std::ios::binary);
      std::istream_iterator<unsigned char> start(is), end;
      std::vector<unsigned char> binary(start, end);
      out.push_back(std::move(binary));
      spdlog::info("Read {} bytes from {}", out.back().size(),
                   entry.path().filename().c_str());
    }
  }
  spdlog::info("Read {} binaries from {}", out.size(), directory.c_str());
}

inline std::string vec2str(std::vector<int>) { return ""; }
inline auto str2vec(std::string const &str) -> std::vector<int> {
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

inline void usage(const std::string &prg) {
  std::cout << "Usage: " << prg
            << " <graph.xml> <configurations/> <schedule.csv>" << std::endl
            << std::endl
            << "\t<graph.xml>: path to a Graphml representation of the task "
               "graph to schedule"
            << std::endl
            << "\t<configurations/>: path to a directory containing at least "
               "one .xclbin"
            << std::endl
            << "\t<schedule.csv>: path to a CSV file containing rows of "
               "'<task_id>,<t_s>,<pe_index>'"
            << std::endl;
}
