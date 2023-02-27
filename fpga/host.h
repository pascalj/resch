#pragma once

#include "boost/graph/graphml.hpp"
#include "boost/property_map/dynamic_property_map.hpp"
#include "json.hpp"
#define CL_HPP_TARGET_OPENCL_VERSION 200
#include "spdlog/spdlog.h"
#include <CL/cl2.hpp>
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
  cl::Kernel kernel;

  void init(const cl::Program &program) {
    cl_int err;
    kernel = cl::Kernel(program, function_name.c_str(), &err);
    spdlog::debug("Created kernel {}: {}", function_name, err == CL_SUCCESS);
  }
};

struct Task {
  uint32_t id;
  std::string label;
  std::vector<uint32_t> cost;

  Task(uint32_t id, const std::string &label, const std::vector<uint32_t> &cost)
      : id(id), label(label), cost(cost) {}
  Task() {}
};

struct ScheduledTask : public Task {
  uint32_t t_s;
  uint32_t pe_id;

  ScheduledTask(const Task &t, uint32_t t_s, uint32_t pe_id)
      : Task(t), t_s(t_s), pe_id(pe_id) {}
};

struct Dependency {
  std::vector<uint32_t> cost;
};

struct Configuration {
  uint32_t id;
  std::string file_name;
  std::vector<PE> PEs;
  cl::Program program;

  // We don't want to copy this ever
  Configuration(uint32_t id, std::string file_name)
      : id(id), file_name(file_name) {}
  Configuration(const Configuration &) = delete;
  Configuration(Configuration &&) = default;
  ~Configuration() = default;

  void init(const cl::Context &context, const cl::Device &device,
            std::filesystem::path directory,
            std::string extension = ".xclbin") {
    auto config_bin_file =
        std::filesystem::directory_entry(directory / (file_name + extension));
    spdlog::info("Attempting to load {}", config_bin_file.path().c_str());
    if (config_bin_file.is_regular_file()) {
      std::ifstream is(config_bin_file.path(), std::ios::binary);
      std::istreambuf_iterator<char> start(is), end;
      std::vector<unsigned char> binary(start, end);
      cl::Program::Binaries bins{{binary}};
      spdlog::info("Read {} bytes from {}", binary.size(),
                   config_bin_file.path().filename().c_str());
      std::vector<cl::Device> devs{{device}};
      cl_int err;

      program = cl::Program(context, devs, bins, nullptr, &err);
      spdlog::debug("Progamming: {}", err == CL_SUCCESS);
    } else {
      auto cl_file =
        std::filesystem::directory_entry(directory / (file_name + ".cl"));
      if(cl_file.is_regular_file()) {
        spdlog::warn("Falling back to GPU/CPU");
        spdlog::info("Compiling file: {}", cl_file.path().c_str());
        std::ifstream is(cl_file.path(), std::ios::in | std::ios::binary);
        std::istreambuf_iterator<char> start(is), end;
        std::string source(start, end);

        cl_int err;
        program = cl::Program(context, source, true, &err);
        spdlog::debug("Progamming: {}", err == CL_SUCCESS);
      } else {
        assert(false);
      }
    }

    for (auto &pe : PEs) {
      spdlog::info("Initializing PE {}", pe.id);
      pe.init(program);
    }
  }
};

struct Machine {
  std::vector<Configuration> configs;
  cl::Device device;

  void init(const cl::Context &context, const cl::Device &in_dev,
            std::filesystem::path directory) {
    device = in_dev;
    for (auto &config : configs) {
      config.init(context, device, directory);
    }
  }

  const PE& pe(uint32_t pe_idx) const {
    for(auto& config : configs) {
      for(auto& pe : config.PEs) {
        if(pe.id == pe_idx) {
          return pe;
        }
      }
    }
    assert(false);
  }

};

// Use a page-aligned vector
template <typename T>
using aligned_vector =
    std::vector<T, boost::alignment::aligned_allocator<T, 4096>>;
// A schedule is the set of ScheduledTasks, since they contain t_s and the PE
using Schedule = std::vector<ScheduledTask>;
using Graph = boost::adjacency_list<boost::vecS, boost::vecS, boost::bidirectionalS,
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
  spdlog::debug("Found {} platforms:", platforms.size());
  for (auto &platform : platforms) {
    spdlog::debug("\t{}", platform.getInfo<CL_PLATFORM_NAME>());
  }
  assert(platforms.size() >= 1);

  // cheap to copy
  platform = platforms[0];
  spdlog::info("Selected {}", platform.getInfo<CL_PLATFORM_NAME>());

  std::vector<cl::Device> devices;
  platform.getDevices(CL_DEVICE_TYPE_ALL, &devices);
  spdlog::debug("Found {} devices:", devices.size());
  for (auto &device : devices) {
    spdlog::debug("\t{}", device.getInfo<CL_DEVICE_NAME>());
  }
  assert(platforms.size() >= 1);

  device = devices[0];
  spdlog::info("Selected {}", device.getInfo<CL_DEVICE_NAME>());

  cl_int err;
  cl::Context device_ctx({device}, nullptr, nullptr, nullptr, &err);
  spdlog::debug("Context: {}", err == CL_SUCCESS);

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
  /* properties.property("id", boost::get(boost::vertex_index, graph)); */
  properties.property("node_id", boost::get(&Task::id, graph));
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
  assert(num_vertices(graph) > 0);
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

  for (auto &task_data : data["schedule"]) {
    auto plain_task = graph[static_cast<int>(task_data["id"])];
    plain_task.id = task_data["id"];
    uint32_t t_s = task_data["t_s"];
    uint32_t pe_id = task_data["PE"];
    schedule.emplace_back(plain_task, t_s, pe_id);
  }
  /* assert(schedule.size() == num_vertices(graph)); */
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
    Configuration config(config_data["id"], config_data["file_name"]);
    for (auto &pe_data : config_data["PEs"]) {
      uint32_t id = pe_data["id"];
      std::string kernel_name = pe_data["function_name"];
      config.PEs.push_back({id, kernel_name});
    }
    machine.configs.push_back(std::move(config));
  }
}

/**
 * @brief Tune parameters for processing and communication cost
 *
 * It executes a range of kernels and measures their execution time, performs a
 * linear regression on it and then returns beta_0 and beta_1.
 *
 * @param ctx The CL context
 * @param dev The CL device
 * @param conf A fitting configuration (any shoul be valid)
 */
std::pair<int, int> tune_parameters(const cl::Context &ctx,
                                     const cl::Device &dev,
                                     Configuration &conf, std::function<void(int, cl::Kernel&)>);


constexpr int max_compsize_shift = 24;
constexpr int max_bufsize_shift = 24;
using Measurement = std::pair<int, int>;
std::pair<int, int> linreg(const std::vector<Measurement>& measurements);

/**
 * @brief Execute a task graph using only the allocation from the schedule
 *
 * This method does not try to delay the execution of tasks, but assignes them
 * only to the assigned PEs and enqueues them. This should be relatively fast,
 * but in theory could be worse than the optimal case.
 *
 * @param context cl::Context
 * @param machine Machine model to use
 * @param graph Graph of tasks to execute
 * @param schedule The schedule with the allocation included
 */
void execute_dag_with_allocation(cl::Context &, const Machine &, const Graph &,
                                 const Schedule &);

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
