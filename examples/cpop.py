from context import resch as r
from resch import machine, graph, optimal
from resch.heft import original, cpop

(g, w, c) = graph.load("graphs/test.xml")

mm_r = machine.get_r([range(w.shape[1])])

S = cpop.build_schedule(g, w, c)
print([(t.t_s, t.t_f, t.pe.index) for t in S.tasks])

