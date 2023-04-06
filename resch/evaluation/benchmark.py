from .metrics import speedup, makespan, slr, slack
import numpy as np
import os
import pandas as pd
import time
import random
from tqdm import tqdm

from resch.evaluation import generator
from resch.graph import taskgraph
from resch.scheduling import optimal, reft, schedule
from test.fixtures import fixtures

def single_benchmark(M, G, algo, benchmark, pbar = None):
    """
    Benchmark one machine with a range of task graphs

    Args:
        M (): machine model
        Gs (): list of TaskGraph
        algo (): algorithm to be applied with algo(M, G)

    Returns:
        Dictionary of metrics for the schedules
    """

    start = time.time()
    (S, E) = algo[1](M, G)
    duration = time.time() - start
    S.validate(G, M)
    (((S, E), G, algo[0], duration))
    if pbar:
        pbar.update(1)

    metrics = pd.DataFrame([list(benchmark.values()) + [
        algo[0],
        duration,
        G.title,
        G.num_nodes(),
        G.num_edges(),
        len(M.locations()),
        len(M.PEs()),
        makespan(S),
        speedup(S, G),
        slr(S, G),
        slack(S, G)]],
      columns=list(benchmark.keys()) + ["benchmark", "runtime", "graph", "num_nodes", "num_edges", "num_locations", "num_pes", "makespan", "speedup", "slr", "slack"])

    # with open("scheds.csv", "a") as f:
    #     for ((S, E), G, t) in SGs:
    #         S.to_csv(f)

    return metrics

def machine_benchmark(M, Gs, algos, benchmark, pbar = None):
    """
    Benchmark one machine with a range of task graphs

    Args:
        M (): machine model
        Gs (): list of TaskGraph
        algo (): algorithm to be applied with algo(M, G)

    Returns:
        Dictionary of metrics for the schedules
    """

    metrics = []

    for G in Gs:
        for algo in algos:
            metrics.append(single_benchmark(M, G, algo, benchmark, pbar))

    return metrics


def benchmark_random_optimal_reft(repetitions):
    Gs = [taskgraph.TaskGraph(generator.random(i)) for i in range(1, 10) for a in range(repetitions)]
    Gs.extend([taskgraph.TaskGraph(generator.erdos(i, 0.2)) for i in range(1, 10) for a in range(repetitions)])
    Gs.extend([taskgraph.TaskGraph(generator.layer_by_layer(i, 3, 0.2)) for i in range(1, 10) for a in range(repetitions)])
    Ms = [("pr", fixtures.pr_machine(1, l)) for l in range(1, 4)]
    Ms.extend([("parallel", fixtures.single_config_machine(p, 1)) for p in range(1, 4)])

    algos = [
            ("optimal", lambda M, G: optimal.OptimalScheduler(M, G, schedule.NoEdgeSchedule).schedule()),
            ("REFT", lambda M, G: reft.REFT(M, G, schedule.NoEdgeSchedule).schedule())]

    pbar = tqdm(desc="random_optimal_reft", total = len(algos) * len(Ms) * len(Gs))
    dfs = []
    for (machine, M) in Ms:
        dfs.extend(machine_benchmark(M, Gs, algos, {"generator": "random", "machine": machine}, pbar))
    return pd.concat(dfs)

def benchmark_random_reconf(repetitions):
    Gs = [taskgraph.TaskGraph(generator.random(i)) for i in range(3, 11) for a in range(repetitions)]
    Gs.extend([taskgraph.TaskGraph(generator.erdos(i, 0.2)) for i in range(3, 11) for a in range(repetitions)])
    Gs.extend([taskgraph.TaskGraph(generator.layer_by_layer(i, 3, 0.2)) for i in range(3, 11) for a in range(repetitions)])
    Ms = [("pr", fixtures.pr_machine(p, l)) for p in range(3, 4) for l in range(1, 4)]

    ntypes = 3

    for G in Gs:
        for task in G.tasks():
            G.set_task_type(task, random.randint(1, ntypes))

    for (machine, M) in Ms:
        assert len(M.PEs()) >= ntypes
        types = [i % ntypes + 1 for i in range(len(M.PEs()))]
        random.shuffle(types)
        for i, pe in enumerate(M.PEs()):
            pe.type = types[i]

    algos = [
            ("optimal", lambda M, G: optimal.OptimalScheduler(M, G, schedule.NoEdgeSchedule).schedule()),
            ("REFT", lambda M, G: reft.REFT(M, G, schedule.NoEdgeSchedule).schedule())]

    overheads = range(0, 200, 10)
    pbar = tqdm(desc="random_reconf", total = len(algos) * len(overheads) * len(Ms) * len(Gs))
    dfs = []
    for overhead in overheads:
        for (machine, M) in Ms:
            for loc in M.locations():
                M.properties[loc]["r"] = overhead
            dfs.extend(machine_benchmark(M, Gs, algos, {"machine": machine, "overhead": overhead}, pbar))
    return pd.concat(dfs)

def benchmark_random_reconf_compare(repetitions):
    Gs = [taskgraph.TaskGraph(generator.random(i)) for i in range(3, 11) for a in range(repetitions)]
    Gs.extend([taskgraph.TaskGraph(generator.erdos(i, 0.2)) for i in range(3, 11) for a in range(repetitions)])
    Gs.extend([taskgraph.TaskGraph(generator.layer_by_layer(i, 3, 0.2)) for i in range(3, 11) for a in range(repetitions)])

    Ms = [("pr", fixtures.pr_machine(p, l)) for p in range(3, 4) for l in range(3, 4)]
    Ms.extend([("r", fixtures.r_machine([p], l)) for p in range(3, 4) for l in range(1, 2)])

    ntypes = 3

    for G in Gs:
        for task in G.tasks():
            G.set_task_type(task, random.randint(1, ntypes))

    for (machine, M) in Ms:
        assert len(M.PEs()) >= ntypes
        types = [i % ntypes + 1 for i in range(len(M.PEs()))]
        random.shuffle(types)
        for i, pe in enumerate(M.PEs()):
            pe.type = types[i]

    algos = [
            ("optimal", lambda M, G: optimal.OptimalScheduler(M, G, schedule.NoEdgeSchedule).schedule()),
            ("REFT", lambda M, G: reft.REFT(M, G, schedule.NoEdgeSchedule).schedule())]

    overheads = range(0, 210, 10)
    pbar = tqdm(desc="random_reconf_compare", total = len(algos) * len(overheads) * len(Ms) * len(Gs))
    dfs = []
    for overhead in overheads:
        for (machine, M) in Ms:
            for loc in M.locations():
                M.properties[loc]["r"] = overhead
            dfs.extend(machine_benchmark(M, Gs, algos, {"machine": machine, "overhead": overhead}, pbar))
    return pd.concat(dfs)

def benchmark_random_params(repetitions):
    Gs = [taskgraph.TaskGraph(generator.random(i)) for i in range(10, 11) for a in range(repetitions)]
    Gs.extend([taskgraph.TaskGraph(generator.erdos(i, 1 / p_i), {"p": 1 / p_i}) for i in range(10, 11) for p_i in range(1, 10) for a in range(repetitions)])
    Gs.extend([taskgraph.TaskGraph(generator.layer_by_layer(i, l, 1 / p_i), {"p": 1 / p_i, "l": l}) for i in range(10, 11) for l in range(1, 11) for p_i in range(1, 10) for a in range(repetitions)])

    Ms = [("pr", fixtures.pr_machine(p, l)) for p in range(3, 4) for l in range(3, 4)]
    Ms.extend([("r", fixtures.r_machine([p], l)) for p in range(3, 4) for l in range(1, 2)])

    ntypes = 3

    for G in Gs:
        for task in G.tasks():
            G.set_task_type(task, random.randint(1, ntypes))

    for (machine, M) in Ms:
        assert len(M.PEs()) >= ntypes
        types = [i % ntypes + 1 for i in range(len(M.PEs()))]
        random.shuffle(types)
        for i, pe in enumerate(M.PEs()):
            pe.type = types[i]

    algos = [
            ("optimal", lambda M, G: optimal.OptimalScheduler(M, G, schedule.NoEdgeSchedule).schedule()),
            ("REFT", lambda M, G: reft.REFT(M, G, schedule.NoEdgeSchedule).schedule())]

    overheads = range(0, 210, 10)
    pbar = tqdm(desc="random_params", total = len(algos) * len(overheads) * len(Ms) * len(Gs))

    dfs = []
    for overhead in overheads:
        for (machine, M) in Ms:
            for loc in M.locations():
                M.properties[loc]["r"] = overhead
            for G in Gs:
                for algo in algos:
                    dfs.append(single_benchmark(M, G, algo, {"machine": machine, "overhead": overhead} | G.parameters, pbar))
    return pd.concat(dfs, ignore_index = True)


if __name__ == "__main__":
    os.makedirs("benchmarks", exist_ok=True)
    if not os.path.exists("benchmarks/random_optimal_reft.csv"):
        with open("benchmarks/random_optimal_reft.csv", "w") as f:
            benchmark_random_optimal_reft(1).to_csv(f, index=False)
    if not os.path.exists("benchmarks/random_reconf.csv"):
        with open("benchmarks/random_reconf.csv", "w") as f:
            benchmark_random_reconf(10).to_csv(f, index=False)
    if not os.path.exists("benchmarks/random_reconf_compare.csv"):
        with open("benchmarks/random_reconf_compare.csv", "w") as f:
            benchmark_random_reconf_compare(10).to_csv(f, index=False)
    if not os.path.exists("benchmarks/random_params.csv"):
        with open("benchmarks/random_params.csv", "w") as f:
            benchmark_random_params(1).to_csv(f, index=False)
