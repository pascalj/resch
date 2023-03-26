from .metrics import speedup, makespan, slr, slack
import numpy as np
import os
import pandas as pd
import time

from resch.evaluation import generator
from resch.graph import taskgraph
from resch.scheduling import optimal, reft, schedule
from test.fixtures import fixtures

def machine_benchmark(M, Gs, algo, benchmark):
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
            print(".", end="", flush=True)
            start = time.time()
            output = algo(M, G)
            SGs.append((output, G, time.time() - start))
            

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

    print("")

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
        dfs.append(machine_benchmark(M, LGs, opt, {"benchmark": "optimal", "generator": "erdos", "machine": machine}))
        dfs.append(machine_benchmark(M, LGs, rft, {"benchmark": "REFT", "generator": "erdos", "machine": machine}))
    return pd.concat(dfs)
    
if __name__ == "__main__":
    df = benchmark_random_optimal_reft(10)
    os.makedirs("benchmarks", exist_ok=True)
    with open("benchmarks/random_optimal_reft.csv", "w") as f:
        df.to_csv(f, index=False)
