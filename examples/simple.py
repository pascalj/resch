from context import resch as r
from resch import machine, graph, optimal
import unittest
import graph_tool.all as gt


mm_pr = machine.get_pr(3, 2)
mm_r = machine.get_r([[0, 1], [2]])
g = graph.TaskGraph(graph.import_dot("graphs/simple.dot"))

S = optimal.build_schedule(mm_pr, g)
S.save_svg("simple_pr.svg", mm_pr)

S = optimal.build_schedule(mm_r, g)
S.save_svg("simple_r.svg", mm_r)

