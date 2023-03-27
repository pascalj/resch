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

def machine_benchmark(M, Gs, algo, benchmark, pbar = None):
    """
    Benchmark one machine with a range of task graphs

    Args:
        M (): machine model
        Gs (): list of TaskGraph
        algo (): algorithm to be applied with algo(M, G)

    Returns:
        Dictionary of metrics for the schedules
    """

    SGs = []
    for G in Gs:
            start = time.time()
            output = algo(M, G)
            SGs.append((output, G, time.time() - start))
            if pbar:
                pbar.update(1)

    metrics = pd.DataFrame([list(benchmark.values()) + [
        t,
        G.num_nodes(),
        G.num_edges(),
        len(M.locations()),
        len(M.PEs()),
        makespan(S),
        speedup(S, G),
        slr(S, G),
        slack(S, G),
    ] for ((S, E), G, t) in SGs],
      columns=list(benchmark.keys()) + ["runtime", "num_nodes", "num_edges", "num_locations", "num_pes", "makespan", "speedup", "slr", "slack"])

    return metrics


def benchmark_random_optimal_reft(repetitions):
    RGs = [taskgraph.TaskGraph(generator.random(i)) for i in range(1, 10) for a in range(repetitions)]
    EGs = [taskgraph.TaskGraph(generator.erdos(i, 0.2)) for i in range(1, 10) for a in range(repetitions)]
    LGs = [taskgraph.TaskGraph(generator.layer_by_layer(i, 3, 0.2)) for i in range(1, 10) for a in range(repetitions)]
    Ms = [("pr", fixtures.pr_machine(1, l)) for l in range(1, 4)]
    Ms.extend([("parallel", fixtures.single_config_machine(p, 1)) for p in range(1, 4)])

    opt = lambda M, G: optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()
    rft = lambda M, G: reft.REFT(M, G, schedule.EdgeSchedule).schedule()

    dfs = []
    for (machine, M) in Ms:
        dfs.append(machine_benchmark(M, RGs, opt, {"benchmark": "optimal", "generator": "random", "machine": machine}))
        dfs.append(machine_benchmark(M, RGs, rft, {"benchmark": "REFT", "generator": "random", "machine": machine}))
        dfs.append(machine_benchmark(M, EGs, opt, {"benchmark": "optimal", "generator": "erdos", "machine": machine}))
        dfs.append(machine_benchmark(M, EGs, rft, {"benchmark": "REFT", "generator": "erdos", "machine": machine}))
        dfs.append(machine_benchmark(M, LGs, opt, {"benchmark": "optimal", "generator": "layer", "machine": machine}))
        dfs.append(machine_benchmark(M, LGs, rft, {"benchmark": "REFT", "generator": "layer", "machine": machine}))
    return pd.concat(dfs)

def benchmark_random_reconf(repetitions):
    RGs = [taskgraph.TaskGraph(generator.random(i)) for i in range(3, 11) for a in range(repetitions)]
    EGs = [taskgraph.TaskGraph(generator.erdos(i, 0.2)) for i in range(3, 11) for a in range(repetitions)]
    LGs = [taskgraph.TaskGraph(generator.layer_by_layer(i, 3, 0.2)) for i in range(3, 11) for a in range(repetitions)]
    Ms = [("pr", fixtures.pr_machine(p, l)) for p in range(3, 4) for l in range(1, 4)]

    ntypes = 3

    for G in RGs:
        for task in G.tasks():
            G.set_task_type(task, random.randint(1, ntypes))

    for (machine, M) in Ms:
        assert len(M.PEs()) >= ntypes
        types = [i % ntypes + 1 for i in range(len(M.PEs()))]
        random.shuffle(types)
        for i, pe in enumerate(M.PEs()):
            pe.type = types[i]

    opt = lambda M, G: optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()
    # rft = lambda M, G: reft.REFT(M, G, schedule.EdgeSchedule).schedule()

    overheads = range(0, 200, 10)
    pbar = tqdm(desc="random_reconf", total = len(overheads) * len(Ms) * len(RGs))
    dfs = []
    for overhead in overheads:
        for (machine, M) in Ms:
            for loc in M.locations():
                M.properties[loc]["r"] = overhead
            dfs.append(machine_benchmark(M, RGs, opt, {"benchmark": "overhead", "generator": "random", "machine": machine, "overhead": overhead}, pbar))
        # dfs.append(machine_benchmark(M, RGs, rft, {"benchmark": "REFT", "generator": "random", "machine": machine}))
        # dfs.append(machine_benchmark(M, EGs, opt, {"benchmark": "overhead", "generator": "erdos", "machine": machine}))
        # dfs.append(machine_benchmark(M, EGs, rft, {"benchmark": "REFT", "generator": "erdos", "machine": machine}))
        # dfs.append(machine_benchmark(M, LGs, opt, {"benchmark": "overhead", "generator": "erdos", "machine": machine}))
        # dfs.append(machine_benchmark(M, LGs, rft, {"benchmark": "REFT", "generator": "erdos", "machine": machine}))
    return pd.concat(dfs)


    
if __name__ == "__main__":
    os.makedirs("benchmarks", exist_ok=True)
    # with open("benchmarks/random_optimal_reft.csv", "w") as f:
    #     benchmark_random_optimal_reft(10).to_csv(f, index=False)
    with open("benchmarks/random_reconf.csv", "w") as f:
        benchmark_random_reconf(1).to_csv(f, index=False)
