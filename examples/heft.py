from context import resch as r
from resch import machine, graph, optimal
from resch.heft import original, la
import numpy as np
import unittest
import graph_tool.all as gt

(g, w, c) = graph.load("graphs/test.xml")

mm_r = machine.get_r([range(w.shape[1])])

S = original.build_schedule(g, w, c)
print([(t.t_s, t.t_f, t.pe.index) for t in S.tasks])

