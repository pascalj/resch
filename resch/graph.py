import graph_tool.all as gt
from graph_tool import topology
from resch.task import Task
from math import sqrt
import numpy as np

def import_dot(file):
    return gt.load_graph(file, fmt="dot")

def load(file):
    """Returns a (g, w, c, t) for a given graph file in GraphML"""
    g = gt.load_graph(file)

    cost = g.vp['cost']
    comm = g.ep['comm']
    num_pes = len(cost[0])
    num_locs = int(sqrt(len(comm[g.edges().next()])))

    w = np.zeros((g.num_vertices(), num_pes))

    for p in range(num_pes):
        for v in g.iter_vertices():
            w[v, p] = cost[v][p]

    c = np.zeros((g.num_vertices(), g.num_vertices(), num_locs, num_locs))

    for f, t, comm in g.iter_edges([g.ep['comm']]):
        for l_f in range(num_locs):
            for l_t in range(num_locs):
                c[f, t, l_f, l_t] = comm[l_f * num_locs + l_t]

        

    return (g, w, c)


def save(g, file):
    g.save(file, fmt="graphml")

def generate_simple(num_pes = 2, num_locs = 1):
    nodes = 6
    deps = [[], [0], [0], [0,1], [2], [1,3,4]]

    g = gt.Graph()

    cost = g.new_vertex_property("vector<int>")
    comm = g.new_edge_property("vector<int>")

    for n in range(nodes):
        v = g.add_vertex()
        cost[v] = [100 + (90 * p) for p in range(num_pes)]

    for n in range(nodes):
        print(n)
        for pred in deps[n]:
            e = g.add_edge(pred, n)
            comm[e] = [0 if a == b else 15 for a in range(num_locs) for b in range(num_locs)]

    g.vp['cost'] = cost
    g.ep['comm'] = comm

    return g




class TaskGraph():
    def __init__(self, g):
        self.g = g
        self.tasks = [Task(v[0], v[1], int(v[2]), g.get_in_neighbors(v[0])) for v in g.iter_vertices([g.vp.vertex_name, g.vp.cost])]

    def sorted_tasks(self):
        s_tasks = topology.topological_sort(self.g)
        name_pmap = self.g.vp.vertex_name
        cost_pmap = self.g.vp.cost
        return [Task(v, name_pmap[v], int(cost_pmap[v]), self.g.get_in_neighbors(v)) for v in s_tasks]
