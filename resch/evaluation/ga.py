from .metrics import speedup, makespan, slr, slack
from resch.machine import optimizer, model

import os
import pandas as pd
import numpy as np
import time
import random
from tqdm import tqdm

from resch.evaluation import generator
from resch.graph import taskgraph
from resch.scheduling import optimal, reft, schedule
from test.fixtures import fixtures

intel_opencl_fpga = {
    'lut': 1866240 - 100000,
    'ff': 3732480 - 275150,
    'ram': 11721 - 467,
    'dsp': 5760 - 0,
    'r': 100
}

lu_pe_properties = {
        0:
    {
        'lut': 10421,
        'ff': 25554,
        'ram': 174,
        'dsp': 6,
        't': 1
    },
    1:
    {
        'lut': 10667,
        'ff': 26992,
        'ram': 154,
        'dsp': 6,
        't': 2
    },
    2:
    {
        'lut': 5454,
        'ff': 12976,
        'ram': 83,
        'dsp': 4,
        't': 3
    },
    3:
    {
        'lut': 5454,
        'ff': 13169 * 100,
        'ram': 80,
        'dsp': 4,
        't': 4
    }
}

def optimize_lu_dr_interco():
    g = taskgraph.TaskGraph(generator.lu(5))

    def simple_chromosome_to_dr(chromosome):
        # PE -> configuration
        locs = [model.Location(0, intel_opencl_fpga)]
        PEs = []
        configs = {}

        for c_idx in set(chromosome):
            configs[c_idx] = model.Configuration(c_idx, locs)
        for p_idx, c_idx in enumerate(chromosome):
            config = configs[c_idx]
            PEs.append(model.PE(p_idx, config))
        pe_props = [[pe, lu_pe_properties[pe.index]] for pe in PEs]

        acc = model.Accelerator(PEs)
        topo = model.Topology.default_from_accelerator(acc)
        m = model.Machine(acc, topo, model.Properties(pe_props, {}, intel_opencl_fpga))

        assert m.properties[PEs[1]]["lut"] > 0

        return m

    def duplication_chromosome_to_dr(k):
        def duplication_chromosome_to_dr_n(chromosome):
            # PE -> configuration
            locs = [model.Location(0, intel_opencl_fpga), model.Location(1, intel_opencl_fpga)]
            PEs = []
            configs = {}

            for p_idx, clones in enumerate(zip(*[iter(chromosome)]*k)):
                for clone_offset, c_idx in enumerate(clones):
                    if c_idx != -1:
                        if c_idx not in configs:
                            configs[c_idx] = model.Configuration(c_idx, locs)
                        config = configs[c_idx]
                        PEs.append(model.PE((p_idx * k) + clone_offset, config, {"original_index": p_idx}))

            pe_props = [[pe, lu_pe_properties[pe.original_index]] for pe in PEs]
            l_props = [[l, intel_opencl_fpga] for l in locs]

            acc = model.Accelerator(PEs)
            topo = model.Topology.default_from_accelerator(acc)
            m = model.Machine(acc, topo, model.Properties(pe_props, {}, l_props))

            assert m.properties[PEs[1]]["lut"] > 0
            assert "r" in m.properties[locs[0]]
            return m

        return duplication_chromosome_to_dr_n



    num_pes = 4
    solutions = []

    for k in range(1, 11):
        ga = optimizer.GA(g, duplication_chromosome_to_dr(k))
        solutions.extend(ga.generate(k=k, n=(k * num_pes)))

    def add_metrics(t):
        S = t[3]
        return (t[0], t[1], t[2], makespan(S), speedup(S, g), slr(S, g), slack(S, g))

    metrics = [add_metrics(solution) for solution in solutions]

    df = pd.DataFrame(metrics, columns=["generation", "solution", "k", "makespan", "speedup", "slr", "slack"])
    df.to_csv("solutions.csv", index=False)
        

# TODO: clean this mess up :-(
def optimize_without_limit():
    g = taskgraph.TaskGraph(generator.random(100))

    def duplication_chromosome_to_dr(k):
        def duplication_chromosome_to_dr_n(chromosome):
            # PE -> configuration
            locs = [model.Location(0, intel_opencl_fpga)]
            PEs = []
            configs = {}

            for p_idx, clones in enumerate(zip(*[iter(chromosome)]*k)):
                for clone_offset, c_idx in enumerate(clones):
                    if c_idx != -1:
                        if c_idx not in configs:
                            configs[c_idx] = model.Configuration(c_idx, locs)
                        config = configs[c_idx]
                        PEs.append(model.PE((p_idx * k) + clone_offset, config, {"original_index": p_idx}))

            l_props = [[l, intel_opencl_fpga] for l in locs]

            acc = model.Accelerator(PEs)
            topo = model.Topology.default_from_accelerator(acc)
            m = model.Machine(acc, topo, model.Properties({}, {}, l_props))

            assert "r" in m.properties[locs[0]]
            return m

        return duplication_chromosome_to_dr_n

    num_pes = 1
    solutions = []

    pygad_solutions = []
    fitnesses = []
    for k in range(5, 6):
        ga = optimizer.GA(g, duplication_chromosome_to_dr(k))
        solutions.extend(ga.generate(k=k, n=(k * num_pes), num_configurations=5, solutions=pygad_solutions, fitnesses=fitnesses))

    def add_metrics(t):
        S = t[3]
        return (t[0], t[1], t[2], makespan(S), speedup(S, g), slr(S, g), slack(S, g), len(np.unique(t[1])))

    metrics = [add_metrics(solution) for solution in solutions]

    sols = []
    for sol, fitness in zip(pygad_solutions, fitnesses):
        sols.append((len(np.unique(sol)), fitness))

    df = pd.DataFrame(sols, columns=["configs", "fitness"])
    df.to_csv("optimize_without_limit.csv")


if __name__ == '__main__':
    # optimize_lu_dr_interco()
    optimize_without_limit()
