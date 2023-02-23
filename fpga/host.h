#pragma once

#include <boost/align/aligned_allocator.hpp>
#include <boost/graph/directed_graph.hpp>
#include <boost/property_map/property_map.hpp>
#include <string>
#include <vector>
#include <iostream>

// Use a page-aligned vector
template <typename T>
using aligned_vector =
    std::vector<T, boost::alignment::aligned_allocator<T, 4096>>;

struct Task {
  std::string label = "";
  std::vector<int> cost;
};

struct Dependency {
  std::vector<int> cost;
};

/* using Graph = boost::directed_graph<Task, Dependency>; */
using Graph = boost::adjacency_list<boost::vecS, boost::vecS, boost::directedS, Task, Dependency>;

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
