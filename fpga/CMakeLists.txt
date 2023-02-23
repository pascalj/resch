cmake_minimum_required(VERSION 3.0)

project(fpga CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_executable(host host.cpp)
target_compile_features(host PUBLIC cxx_std_17)
find_package(OpenCL REQUIRED)
find_package(spdlog REQUIRED)
find_package(Boost REQUIRED COMPONENTS graph)

target_link_libraries(host PRIVATE stdc++fs spdlog::spdlog OpenCL Boost::graph )
target_compile_options(host PRIVATE $<$<CONFIG:Debug>:-fsanitize=address,undefined -fno-omit-frame-pointer>)
target_link_options(host PRIVATE $<$<CONFIG:Debug>:-fsanitize=address,undefined -fno-omit-frame-pointer>)
