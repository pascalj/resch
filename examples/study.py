from graph_tool import load_graph
from context import resch
from resch.graph.taskgraph import TaskGraph
from resch.scheduling.optimal import OptimalScheduler
from resch.machine.model import *
from numpy import random
import pandas as pd

g = load_graph("examples/study.xml.gz")
t = TaskGraph(g)

def get_pr():
    locations = [Location(0), Location(1)]
    configs = [Configuration(0, locations), Configuration(1, locations), Configuration(2, locations)]
    PEs = [PE(0, configs[0]), PE(1, configs[1]), PE(2, configs[2])]
    acc = Accelerator(PEs)

    props = Properties()
    props[PEs[0]]["t"] = 1
    props[PEs[1]]["t"] = 2
    props[PEs[2]]["t"] = 3
    for l in locations:
        props[l]["r"] = 10 
    return Machine(acc, Topology.default_from_accelerator(acc), props)

def get_r():
    locations = [Location(0)]
    configs = [Configuration(0, locations), Configuration(1, locations)]
    PEs = [PE(0, configs[0]), PE(1, configs[0]), PE(2, configs[1])]
    acc = Accelerator(PEs)

    props = Properties()
    props[PEs[0]]["t"] = 1
    props[PEs[1]]["t"] = 2
    props[PEs[2]]["t"] = 3
    props[locations[0]]["r"] = 10 
    return Machine(acc, Topology.default_from_accelerator(acc), props)




def get_speedups():
    Gs = []
    for i in range(100):
        g = Graph(t.g)
        new_cost = random.normal(loc=100, scale=10, size=(g.num_vertices(), 3))
        for v in g.get_vertices():
            g.vp["cost"][v] = new_cost[int(v)]
        Gs.append(TaskGraph(g))

    log = pd.DataFrame(columns=["machine", "makespan", "cost"])
    for g in Gs:
        sum = g.w_bar.sum()
        (S, E) = OptimalScheduler(M_pr, t).schedule()
        log.append({"machine": "pr", "makespan": S.length(), "cost": sum}, ignore_index=True)
        (S, E) = OptimalScheduler(M_r, t).schedule()
        log.append({"machine": "r", "makespan": S.length(), "cost": sum}, ignore_index=True)
    with open("study_speedups.csv", "w") as f:
        # TODO: log is empty!
        log.to_csv(f)

M_pr = get_pr()
M_r = get_r()
with open("study_pr.csv", "w") as f:
    (S, E) = OptimalScheduler(M_pr, t).schedule()
    S.to_csv(f)
with open("study_r.csv", "w") as f:
    (S, E) = OptimalScheduler(M_r, t).schedule()
    S.to_csv(f)
get_speedups()
