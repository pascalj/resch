from .metrics import speedup, makespan, slr, slack, efficiency
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
        'ff': 1316900,
        'ram': 80,
        'dsp': 4,
        't': 4
    }
}

def random_pe_properties(num_pes):
    return {
        'lut': random.randrange(int(intel_opencl_fpga["lut"] / num_pes )),
        'ff': random.randrange(int(intel_opencl_fpga["ff"] / num_pes )),
        'ram': random.randrange(int(intel_opencl_fpga["ram"] / num_pes )),
        'dsp': random.randrange(int(intel_opencl_fpga["dsp"] / num_pes ))
    }


def optimize_lu_dr_interco():
    g = taskgraph.TaskGraph(generator.lu(6))

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

    gene_space = []
    for i in range(n):
        if i % k == 0:
            gene_space.append(list(range(0, num_configurations+1)))
        else:
            gene_space.append(list(range(-1, num_configurations+1)))

    for k in range(1, 11):
        ga = optimizer.GA(g, duplication_chromosome_to_dr(k))
        solutions.extend(ga.generate(k=k, n=(k * num_pes)))

    def add_metrics(t):
        S = t[3]
        return (t[0], t[1], t[2], makespan(S), speedup(S, g), slr(S, g), slack(S, g), efficiency(S, c))

    metrics = [add_metrics(solution) for solution in solutions]

    df = pd.DataFrame(metrics, columns=["generation", "solution", "k", "makespan", "speedup", "slr", "slack", "usage"])
    df.to_csv("optimize_lu_dr_interco.csv", index=False)
        


def optimize_lu_dr_intraco():
    g = taskgraph.TaskGraph(generator.lu(7))

    def pe_genes(chromosome, p_idx):
        return chromosome[p_idx:p_idx + 1]

    def update_pe_properties(pe_properties, genes):
        # { 'lut': 5454, 'ff': 1316900, 'ram': 80, 'dsp': 4, 't': 4 }
        simd_width = genes[0]
        assert(simd_width > 0)
        t = pe_properties['t']
        new_properties = dict(map(lambda i: (i[0], simd_width * i[1]), pe_properties.items()))
        new_properties['t'] = t
        new_properties['factor'] = simd_width
        return new_properties

    def chromosome_to_dr(chromosome):
        # PE -> configuration
        locs = [model.Location(0, intel_opencl_fpga)]
        PEs = []
        configs = [model.Configuration(0, locs)]
        config = configs[0]

        for p_idx in range(4):
            PEs.append(model.PE(p_idx, config, {"original_index": p_idx}))

        pe_props = [[pe, update_pe_properties(lu_pe_properties[pe_id], pe_genes(chromosome, pe_id))] for pe_id, pe in enumerate(PEs)]
        l_props = [[l, intel_opencl_fpga] for l in locs]

        acc = model.Accelerator(PEs)
        topo = model.Topology.default_from_accelerator(acc)
        m = model.Machine(acc, topo, model.Properties(pe_props, {}, l_props, intel_opencl_fpga))

        assert m.properties[PEs[1]]["lut"] > 0
        assert "r" in m.properties[locs[0]]
        return m

    num_pes = 4
    solutions = []

    gene_space = []
    for i in range(num_pes):
        gene_space.append([1, 2, 4, 8])

    ga = optimizer.GA(g, chromosome_to_dr)
    solutions.extend(ga.generate(gene_space, n = num_pes, num_configurations = 1))

    def add_metrics(t):
        S = t[3]
        return (t[0], t[1], t[2], makespan(S), speedup(S, g), slr(S, g), slack(S, g), efficiency(S, g, ga.chromosome_to_mm(t[1])))

    metrics = [add_metrics(solution) for solution in solutions]

    df = pd.DataFrame(metrics, columns=["generation", "solution", "k", "makespan", "speedup", "slr", "slack", "efficiency"])
    df.to_csv("optimize_lu_dr_intraco.csv", index=False)
        

def optimize_random_intraco():
    gs = [taskgraph.TaskGraph(generator.layer_by_layer(100, 10, 0.2)) for i in range(100)]

    num_pes = 9

    def pe_genes(chromosome, p_idx):
        return chromosome[p_idx:p_idx + 1]

    def update_pe_properties(pe_properties, genes):
        simd_width = genes[0]
        assert(simd_width > 0)
        t = pe_properties.get('t', None)
        new_properties = dict(map(lambda i: (i[0], simd_width * i[1]), pe_properties.items()))
        new_properties['t'] = t
        new_properties['factor'] = simd_width
        return new_properties

    def define_chromosome():
        pe_properties = [random_pe_properties(num_pes) for i in range(9)]     
        def chromosome_to_dr(chromosome):
            # PE -> configuration
            locs = [model.Location(0, intel_opencl_fpga)]
            PEs = []
            configs = [model.Configuration(0, locs)]
            config = configs[0]

            for p_idx in range(num_pes):
                PEs.append(model.PE(p_idx, config, {"original_index": p_idx}))

            pe_props = [[pe, update_pe_properties(pe_properties[pe_id], pe_genes(chromosome, pe_id))] for pe_id, pe in enumerate(PEs)]
            l_props = [[l, intel_opencl_fpga] for l in locs]

            acc = model.Accelerator(PEs)
            topo = model.Topology.default_from_accelerator(acc)
            m = model.Machine(acc, topo, model.Properties(pe_props, {}, l_props, intel_opencl_fpga))

            assert m.properties[PEs[1]]["lut"] > 0
            assert "r" in m.properties[locs[0]]
            return m

        return chromosome_to_dr

    gene_space = []
    for i in range(num_pes):
        gene_space.append([1, 1, 1, 2, 4, 8])
    initial_population = [[1] * num_pes] * 10

    metrics = []
    solutions = []
    for g_idx, g in enumerate(gs):
        ga = optimizer.GA(g, define_chromosome())
        solutions.extend(ga.generate(gene_space, n = num_pes, num_configurations = 1, initial_population=initial_population))

        def add_metrics(t):
            S = t[3]
            return (t[0], t[1], t[2], makespan(S), speedup(S, g), slr(S, g), slack(S, g), efficiency(S, g, ga.chromosome_to_mm(t[1])), g_idx)

    metrics = [add_metrics(solution) for solution in solutions]
    df = pd.DataFrame(metrics, columns=["generation", "solution", "k", "makespan", "speedup", "slr", "slack", "efficiency", "graph"])
    df.to_csv("optimize_random_intraco.csv", index=False)

def optimize_random_co(num_graphs = 100, num_configs = 3, r = 100):
    gs = [taskgraph.TaskGraph(generator.layer_by_layer(100, 5, 0.2)) for i in range(num_graphs)]
    num_pes = 9

    def pe_genes(chromosome, p_idx):
        return chromosome[p_idx * 2:(p_idx * 2) + 2]

    def update_pe_properties(pe_properties, genes):
        configuration = genes[0]
        simd_width = genes[1]
        assert(simd_width > 0)
        t = pe_properties.get('t', None)
        new_properties = dict(map(lambda i: (i[0], simd_width * i[1]), pe_properties.items()))
        new_properties['t'] = t
        new_properties['factor'] = simd_width
        return new_properties

    def define_chromosome():
        pe_properties = [random_pe_properties(num_pes) for i in range(num_pes)]     
        def chromosome_to_dr(chromosome):
            # PE -> configuration
            intel_opencl_fpga["r"] = r
            locs = [model.Location(0, intel_opencl_fpga)]
            PEs = []
            configs = [model.Configuration(config_idx, locs) for config_idx in range(num_configs)]

            for p_idx in range(num_pes):
                (pe_config, _) = pe_genes(chromosome, p_idx)
                PEs.append(model.PE(p_idx, configs[pe_config], {"original_index": p_idx}))

            pe_props = [[pe, update_pe_properties(pe_properties[pe_id], pe_genes(chromosome, pe_id))] for pe_id, pe in enumerate(PEs)]
            l_props = [[l, intel_opencl_fpga] for l in locs]

            acc = model.Accelerator(PEs)
            topo = model.Topology.default_from_accelerator(acc)
            m = model.Machine(acc, topo, model.Properties(pe_props, {}, l_props, intel_opencl_fpga))

            assert m.properties[PEs[1]]["lut"] > 0
            assert "r" in m.properties[locs[0]]
            return m

        return chromosome_to_dr

    gene_space = []
    for i in range(num_pes):
        gene_space.append(range(num_configs))
        gene_space.append([1, 2, 4, 8])

    initial_population = [[0, 1] * num_pes] * (2 * num_pes)

    metrics = []
    solutions = []
    for g_idx, g in enumerate(gs):
        ga = optimizer.GA(g, define_chromosome())
        for row in ga.generate(gene_space, initial_population=initial_population):
            solutions.append(row + (g_idx,))

    def add_metrics(t):
        S = t[3]
        g_idx = t[5]
        return (t[0], t[1], t[2], makespan(S), speedup(S, g), slr(S, g), slack(S, g), efficiency(S, g, ga.chromosome_to_mm(t[1])), g_idx, r, num_configs)

    metrics = [add_metrics(solution) for solution in solutions]
    df = pd.DataFrame(metrics, columns=["generation", "solution", "k", "makespan", "speedup", "slr", "slack", "efficiency", "graph", "r", "num_configs"])
    df.to_csv("optimize_random_co.csv", index=False, mode="a")


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
    # optimize_lu_dr_intraco()
    # optimize_random_intraco()
    optimize_random_co(num_configs=1, r = 0, num_graphs = 3)
    optimize_random_co(num_configs=2, r = 0, num_graphs = 3)
    optimize_random_co(num_configs=3, r = 0, num_graphs = 3)
    # optimize_without_limit()
