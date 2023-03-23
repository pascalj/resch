import numpy as np
from .metrics import speedup, makespan, slr, slack

from resch.evaluation import generator
from resch.graph import taskgraph
from test.fixtures import fixtures
from resch.scheduling import optimal, reft, schedule

def machine_benchmark(M, Gs, algo):
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

    metrics = np.array([[
        makespan(S),
        speedup(S, G),
        slr(S, G),
        slack(S, G),
    ] for ((S, E), G) in SGs])

    return metrics


def benchmark_reft_against_optimal():
    Gs = [taskgraph.TaskGraph(generator.random(10)) for i in range(10)]
    M = fixtures.pr_machine(2, 2)

    opt = lambda M, G: optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()
    rft = lambda M, G: reft.REFT(M, G, schedule.EdgeSchedule).schedule()
    opt_results = machine_benchmark(M, Gs, opt)
    reft_results = machine_benchmark(M, Gs, rft)

    print(opt_results)
    print(reft_results)
    
if __name__ == "__main__":
    benchmark_reft_against_optimal()
