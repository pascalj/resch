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
    locations = [m.Location(0)]
    config = m.Configuration(0, locations)
    PEs = [m.PE(0, config, {})]
    return m.MachineModel(PEs)

def instance(pe, location, interval):
    return s.Instance(pe, location, interval)

def task_with_len(slen):
    machine = minimal_machine()
    task = s.Task(0, "task", slen, [])
    interval = po.closedopen(0, slen)
    return s.ScheduledTask(task, interval, instance(machine.get_pe(0), m.Location(0), instance))

def schedule_with_len(slen):
    S = s.Schedule()
    S.add_task(task_with_len(slen))
    return S

def empty_graph():
    g = Graph()
    w = np.zeros((0,0))
    c = np.zeros((0,0,0,0))
    t = np.zeros((0))
    return (g, w, c, t)

def sample_graph():
    return graph.load("tests/fixtures/sample.xml")

