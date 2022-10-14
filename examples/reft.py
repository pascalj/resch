from context import resch
from resch import machine, graph, printer
from resch.heft import original, reft

import graph_tool.all as gt

(g, w, c) = graph.load("graphs/basic_lu.xml")

mm_r = machine.get_r([[0, 1], [2,3]])

S = reft.build_schedule(g, w, c, mm_r)
graph.save_pdf(g, "graphs/basic_lu.pdf")
printer.save_schedule(S, "schedules/ref_basic_lu.svg", mm_r)
