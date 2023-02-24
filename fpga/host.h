#pragma once

#include "boost/graph/graphml.hpp"
#include "boost/property_map/dynamic_property_map.hpp"
#include "json.hpp"
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

struct PE {
  uint32_t id;
  std::string function_name;
};

struct Task {
  uint32_t id;
  std::string label;
  std::vector<uint32_t> cost;
};

struct ScheduledTask : public Task {
  uint32_t t_s;
  PE pe;

  ScheduledTask(const Task &t, uint32_t t_s, PE pe)
      : Task(t), t_s(t_s), pe(pe) {}
};

struct Dependency {
  std::vector<uint32_t> cost;
};


struct Configuration {
  uint32_t id;
  std::string file_name;
  std::vector<PE> PEs;
};

struct Machine {
  std::vector<Configuration> configs;
};

// Use a page-aligned vector
template <typename T>
using aligned_vector =
    std::vector<T, boost::alignment::aligned_allocator<T, 4096>>;
// A schedule is the set of ScheduledTasks, since they contain t_s and the PE
using Schedule = std::vector<ScheduledTask>;
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

/**
 * @brief Helper function to get the first device from the first platform
 *
 * @param context Context to be set (to the device ctx)
 * @param platform Platform to be set (to the first platform found)
 * @param device Device to be set
 */
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
inline std::string vec2str(std::vector<uint32_t>);
inline auto str2vec(std::string const &str) -> std::vector<uint32_t>;

/**
 * @brief Read the task graph from GraphML
 *
 * @param graph_path Path to the task graph XML
 * @param graph Empty graph object
 * @param properties Empty dynamic_properties
 */
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

/**
 * @brief Read the schedule from JSON
 *
 * @param schedule_path Path to the JSON file
 * @param graph Task graph to construct the ScheduledTasks from
 * @param schedule Schedule to be constructed
 */
inline void read_schedule(const std::filesystem::path &schedule_path,
                          const Graph &graph, Schedule &schedule) {
  using json = nlohmann::json;
  std::ifstream is(schedule_path, std::ios::binary);
  json data = json::parse(is);

  auto tasks = vertices(graph);
  // TODO: maybe put this into a map as it's currently N^2
  auto find_task_by_id = [tasks, &graph](uint32_t task_id) {
    auto task_it = std::find_if(tasks.first, tasks.second,
                                [task_id, &graph](const auto &task) {
                                  return graph[task].id == task_id;
                                });
    // We screwed up if the task's id is unknown.
    assert(task_it != tasks.second);
    return graph[*task_it];
  };

  for (auto &task_data : data["schedule"]) {
    auto plain_task = find_task_by_id(task_data["id"]);
    uint32_t t_s = task_data["t_s"];
    PE pe{task_data["PE"]};
    schedule.emplace_back(plain_task, t_s, pe);
  }
}

/**
 * @brief Read the machine model from JSON
 *
 * @param machine_path Path to JSON (may be same as schedule_path)
 * @param machine Empty machine model
 */
inline void read_machine_model(const std::filesystem::path &machine_path,
                               Machine &machine) {
  using json = nlohmann::json;
  std::ifstream is(machine_path, std::ios::binary);
  json data = json::parse(is);

  for (auto &config_data : data["configurations"]) {
    Configuration config;
    config.id = config_data["id"];
    config.file_name = config_data["file_name"];
    for (auto &pe_data : config_data["PEs"]) {
      uint32_t id = pe_data["id"];
      std::string kernel_name = pe_data["function_name"];

      config.PEs.push_back({id, kernel_name});
    }
    machine.configs.push_back(std::move(config));
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
void execute_dag_with_schedule(cl::Context &context, cl::Device &device,
                               const Graph &graph, const Schedule &schedule);

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

inline std::string vec2str(std::vector<uint32_t>) { return ""; }
inline auto str2vec(std::string const &str) -> std::vector<uint32_t> {
  auto number = 0;
  auto out = str;
  auto vec = std::vector<uint32_t>{};
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
