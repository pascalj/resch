import numpy as np
import pandas as pd
import os
from .metrics import speedup, makespan, slr, slack

from resch.evaluation import generator
from resch.graph import taskgraph
from test.fixtures import fixtures
from resch.scheduling import optimal, reft, schedule

def machine_benchmark(M, Gs, algo, title):
    """
    Benchmark one machine with a range of task graphs

    Args:
        M (): machine model
        Gs (): list of TaskGraph
        algo (): algorithm to be applied with algo(M, G)

    Returns:
        Dictionary of metrics for the schedules
    """
    
    SGs = [(algo(M, G), G) for G in Gs]

    metrics = pd.DataFrame([[
        title,
        G.num_nodes(),
        G.num_edges(),
        len(M.locations()),
        len(M.PEs()),
        makespan(S),
        speedup(S, G),
        slr(S, G),
        slack(S, G),
    ] for ((S, E), G) in SGs],
      columns=["benchmark", "num_nodes", "num_edges", "num_locations", "num_pes", "makespan", "speedup", "slr", "slack"])

    return metrics


def benchmark_random_optimal_reft():
    Gs = [taskgraph.TaskGraph(generator.random(10)) for i in range(1, 10)]
    Ms = [fixtures.pr_machine(p, l) for p in range(1, 5) for l in range(1, 5)]

    opt = lambda M, G: optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()
    rft = lambda M, G: reft.REFT(M, G, schedule.EdgeSchedule).schedule()

    dfs = []
    for M in Ms:
        dfs.append(machine_benchmark(M, Gs, opt, "optimal"))
        dfs.append(machine_benchmark(M, Gs, rft, "REFT"))

    return pd.concat(dfs)
    
if __name__ == "__main__":
    df = benchmark_random_optimal_reft()
    os.makedirs("benchmarks", exist_ok=True)
    with open("benchmarks/random_optimal_reft.csv", "w") as f:
        df.to_csv(f, index=False)
