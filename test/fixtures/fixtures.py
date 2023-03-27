from ..context import resch

import resch.scheduling as s
import resch.machine as m
import resch.graph as graph
import portion as po
from graph_tool import Graph
import numpy as np

def empty_schedule():
    return s.Schedule()

def minimal_machine():
    return single_config_machine(num_PEs = 1, num_locs = 1)

def single_config_machine(num_PEs = 1, num_locs = 1):
    locations = [m.Location(i) for i in range(num_locs)]
    config = m.Configuration(0, locations)
    PEs = [m.PE(i, config, {}) for i in range(num_PEs)]
    acc = m.Accelerator(PEs)
    topo = m.Topology.default_from_accelerator(acc)
    return m.Machine(acc, topo, m.Properties())

def pr_machine(num_PEs = 1, num_locs = 1):
    locations = [m.Location(i) for i in range(num_locs)]
    configs = [m.Configuration(i, locations) for i in range(num_PEs)]
    PEs = [m.PE(i, configs[i], {}) for i in range(num_PEs)]
    acc = m.Accelerator(PEs)
    topo = m.Topology.default_from_accelerator(acc)
    return m.Machine(acc, topo, m.Properties())

def r_machine(config_to_pes, num_locs = 1):
    locations = [m.Location(i) for i in range(num_locs)]
    configs = [m.Configuration(i, locations) for i in range(len(config_to_pes))]
    PEs = []
    for config_id, num_pes in enumerate(config_to_pes):
        for _ in range(num_pes):
            PEs.append(m.PE(len(PEs), configs[config_id], {}))

    acc = m.Accelerator(PEs)
    topo = m.Topology.default_from_accelerator(acc)
    return m.Machine(acc, topo, m.Properties())

def instance(task, pe, location, interval):
    return s.Instance(task, pe, location, interval)

def task_with_len(slen):
    machine = minimal_machine()
    task = s.Task(0, "task", slen, [])
    interval = po.closedopen(0, slen)
    return s.ScheduledTask(task, instance(task, machine.get_pe(0), m.Location(0), interval))

def schedule_with_len(slen):
    S = s.Schedule()
    S.add_task(task_with_len(slen))
    return S

def empty_graph():
    g = Graph()
    return graph.TaskGraph(g)

def sample_graph():
    return graph.load("test/fixtures/sample.xml")


