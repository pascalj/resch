import graph_tool.all as gt
from graph_tool import topology
from resch.task import Task

def import_dot(file):
    return gt.load_graph(file, fmt="dot")

def save_dot(g, file):
    gt.save_graph(file, fmt="dot")

class TaskGraph():
    def __init__(self, g):
        self.g = g
        self.tasks = [Task(v[0], v[1], int(v[2]), g.get_in_neighbors(v[0])) for v in g.iter_vertices([g.vp.vertex_name, g.vp.cost])]

    def sorted_tasks(self):
        s_tasks = topology.topological_sort(self.g)
        name_pmap = self.g.vp.vertex_name
        cost_pmap = self.g.vp.cost
        return [Task(v, name_pmap[v], int(cost_pmap[v]), self.g.get_in_neighbors(v)) for v in s_tasks]
