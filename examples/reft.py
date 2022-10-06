from context import resch
from resch import machine, graph
from resch.heft import original, reft

(g, w, c) = graph.load("graphs/test.xml")

mm_r = machine.get_r([range(w.shape[1])])

S = reft.build_schedule(g, w, c, mm_r)
print([(t.t_s, t.t_f, t.pe.index) for t in S.tasks])

