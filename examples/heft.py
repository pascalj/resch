from context import resch as r
from resch import machine, graph, optimal, heft
from resch import list as ls
import numpy as np
import unittest
import graph_tool.all as gt


mm_r = machine.get_r([[0, 1]])
g = graph.import_dot("graphs/simple.dot")
tg = graph.TaskGraph(g)

w_heft = np.array([[100, 100] for _ in g.iter_vertices()])
c_heft = np.zeros((g.num_vertices(), g.num_vertices(), len(mm_r.PEs), len(mm_r.PEs)))

# We have a cost of 15 for all tasks between PEs
for f in g.iter_vertices():
    for t in g.iter_vertices():
        for p_f in range(len(mm_r.PEs)):
            for p_t in range(len(mm_r.PEs)):
                if f != t and p_f != p_t:
                    c_heft[f, t, p_f, p_t] = 15

S = heft.build_schedule(g, w_heft, c_heft)
S.save_svg("heft_simple_r.svg", mm_r, print_locs = False)
