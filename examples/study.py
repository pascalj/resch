from graph_tool import load_graph
from context import resch
from resch.graph.taskgraph import TaskGraph
from resch.scheduling.optimal import OptimalScheduler
from resch.scheduling.schedule import EdgeSchedule
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

def get_combined():
    locations = [Location(0)]
    configs = [Configuration(0, locations)]
    PEs = [PE(0, configs[0]), PE(1, configs[0]), PE(2, configs[0])]
    acc = Accelerator(PEs)

    props = Properties()
    props[PEs[0]]["t"] = 1
    props[PEs[1]]["t"] = 2
    props[PEs[2]]["t"] = 3
    props[locations[0]]["r"] = 0
    return Machine(acc, Topology.default_from_accelerator(acc), props)


def get_speedups():
    Gs = []
    for i in range(100):
        g = Graph(t.g)
        new_cost = random.normal(loc=100, scale=10, size=(g.num_vertices(), 3))
        for v in g.get_vertices():
            g.vp["cost"][v] = new_cost[int(v)]
        Gs.append(TaskGraph(g))

    logs = [pd.DataFrame(columns=["machine", "makespan", "cost", "overhead"])]
    for o in range(0, 210, 10):
        for l in M_pr.locations():
            M_pr.properties[l]["r"] = int(o / len(M_pr.locations()))
        for l in M_r.locations():
            M_r.properties[l]["r"] = o
        for l in M_c.locations():
            M_r.properties[l]["r"] = o
        for g in Gs:
            sum = g.w_bar.sum()
            (S, E) = OptimalScheduler(M_pr, g).schedule()
            logs.append(pd.DataFrame([["pr", S.length(), sum, o]], columns=["machine", "makespan", "cost", "overhead"]))
            (S, E) = OptimalScheduler(M_r, g).schedule()
            logs.append(pd.DataFrame([["r", S.length(), sum, o]], columns=["machine", "makespan", "cost", "overhead"]))
            (S, E) = OptimalScheduler(M_c, g).schedule()
            logs.append(pd.DataFrame([["c", S.length(), sum, o]], columns=["machine", "makespan", "cost", "overhead"]))
    log = pd.concat(logs, ignore_index=True)
    with open("study_speedups.csv", "w") as f:
        # TODO: log is empty!
        log.to_csv(f)

def get_combined_speedups():
    Gs = []
    for i in range(100):
        g = Graph(t.g)
        new_cost = random.normal(loc=100, scale=10, size=(g.num_vertices(), 3))
        for v in g.get_vertices():
            g.vp["cost"][v] = new_cost[int(v)]
        Gs.append(TaskGraph(g))

    logs = [pd.DataFrame(columns=["machine", "makespan", "cost", "overhead"])]
    for g in Gs:
        sum = g.w_bar.sum()
        (S, E) = OptimalScheduler(M_c, g).schedule()
        logs.append(pd.DataFrame([[False, S.length(), sum, 0]], columns=["edge", "makespan", "cost", "overhead"]))
        (S, E) = OptimalScheduler(M_c, g, EdgeSchedule).schedule()
        logs.append(pd.DataFrame([[True, S.length(), sum, 0]], columns=["edge", "makespan", "cost", "overhead"]))

    Gs = []
    for i in range(100):
        g = Graph(t.g)
        new_cost = random.normal(loc=100, scale=10, size=(g.num_vertices(), 3))
        for v in g.get_vertices():
            g.vp["cost"][v] = new_cost[int(v)]
        Gs.append(TaskGraph(g))

    log = pd.concat(logs, ignore_index=True)
    with open("study_combined.csv", "w") as f:
        # TODO: log is empty!
        log.to_csv(f)

M_pr = get_pr()
M_r = get_r()
M_c = get_combined()
with open("study_pr.csv", "w") as f:
    (S, E) = OptimalScheduler(M_pr, t).schedule()
    S.to_csv(f)
with open("study_r.csv", "w") as f:
    (S, E) = OptimalScheduler(M_r, t).schedule()
    S.to_csv(f)
# get_speedups()
get_combined_speedups()
