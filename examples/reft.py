from context import resch
from resch import machine, graph, printer
from resch.heft import original, reft


(g, w, c) = graph.load("graphs/basic_lu.xml")

mm_r = machine.get_r([[0, 1], [2,3]], range(2))

S = reft.build_schedule(g, w, c, mm_r)
graph.save_pdf(g, "graphs/basic_lu.pdf")
with open('schedules/ref_basic_lu.svg', 'w') as file:
    printer.save_schedule(S, file, mm_r)
