cmake_minimum_required(VERSION 3.8)

project(fpga CXX)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

option(RESCH_SANITIZE "ADD SANITIZERS" OFF)

add_executable(host host.cpp)
target_compile_features(host PUBLIC cxx_std_17)
find_package(OpenCL REQUIRED)

include(FetchContent)

# Get dependencies
FetchContent_Declare(
  Boost
  GIT_REPOSITORY https://github.com/boostorg/boost.git
  GIT_TAG boost-1.80.0
  GIT_PROGRESS TRUE
)
FetchContent_Declare(
  spdlog
  GIT_REPOSITORY https://github.com/gabime/spdlog.git
  GIT_TAG        v1.9.2
  GIT_PROGRESS TRUE
)
FetchContent_MakeAvailable(Boost)
FetchContent_MakeAvailable(spdlog)

target_link_libraries(host PRIVATE stdc++fs spdlog::spdlog OpenCL Boost::graph )

if (RESCH_SANITIZE)
        target_compile_options(host PRIVATE $<RESCH_SANITIZE:-fsanitize=address,undefined -fno-omit-frame-pointer>)
        target_link_options(host PRIVATE $<RESCH_SANITIZE:-fsanitize=address,undefined -fno-omit-frame-pointer>)
endif(RESCH_SANITIZE)

target_compile_options(host PRIVATE $<$<CONFIG:DEBUG>:-fno-omit-frame-pointer>)
