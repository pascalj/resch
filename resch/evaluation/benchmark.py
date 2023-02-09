import numpy as np
from .metrics import speedup, makespan, slr, slack

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
    ] for (S, G) in SGs])

    return metrics
