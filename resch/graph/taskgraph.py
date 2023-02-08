import numpy as np
import pdb
from math import sqrt
from graph_tool.topology import topological_sort, shortest_path
 
class TaskGraph:
    def __init__(self, g):
        (g, w, c, t) = self.from_graph(g)
        self.g = g
        self.w = w
        self.c = c
        self.t = t
        self.w_bar = self.w.mean(axis=1)
        self.c_bar = self.c.mean(axis=(2,3))

    def from_graph(self, g):
        if 'cost' in g.vp:
            cost = g.vp['cost']
            num_pes = len(cost[0])
            w = np.zeros((g.num_vertices(), num_pes))

            for p in range(num_pes):
                for v in g.iter_vertices():
                    w[v, p] = cost[v][p]
        else:
            w = np.zeros((g.num_vertices(), 1))


        t = np.zeros((g.num_vertices()))

        if 'type' in g.vp:
            ttype = g.vp['type']
            for v in g.iter_vertices():
                t[v] = ttype[v]


        if 'comm' in g.ep:
            com_cost = g.ep['comm']
            num_locs = int(sqrt(len(com_cost[g.edges().next()])))
            c = np.zeros((g.num_vertices(), g.num_vertices(), num_locs, num_locs))
            for f, t, edge_cost in g.iter_edges([com_cost]):
                for l_f in range(num_locs):
                    for l_t in range(num_locs):
                        c[f, t, l_f, l_t] = edge_cost[l_f * num_locs + l_t]
        else:
            c = np.zeros((g.num_vertices(), g.num_vertices(), 1, 1))
        return (g, w, c, t)

    """ Length of the critical path in terms of w and c """

    def cp_len(self, weights=None):
        g = self.g
        if g.num_vertices() == 0:
            return 0;

        if weights is None:
            weights = self.urank_map()

        cp = self.cp(weights=weights)

        return sum(weights[e] for e in cp)

    """ Returns the edge list of the critical path """

    def cp(self, weights=None):
        first = self.entry_node()
        last = self.exit_node()

        if weights is None:
            weights = self.urank_map()

        nodes, edges = shortest_path(self.g, source=self.entry_node(), target=self.exit_node(), weights=weights)

        return edges

    """ The entry node (a node without in dependencies) """

    def entry_node(self):
        sort = topological_sort(self.g)
        return self.g.vertex(sort[0])

    """ The exit node (a node without out dependencies) """
    def exit_node(self):
        sort = topological_sort(self.g)
        return self.g.vertex(sort[-1])

    """ Returns an edge property map with the upper rank computed"""

    def urank_map(self):
        # Accumulated cost (source node weight + edge weight)
        g = self.g
        weight_map = g.new_edge_property("int32_t", np.iinfo(np.int32).max)
        for v, v_idx in g.iter_vertices([g.vertex_index]):
           for f, t, e_idx, cost in g.iter_out_edges(v, [g.edge_index, g.ep['comm']]):
               res = self.w_bar[v_idx] + self.c_bar[f][t]
               weight_map[g.edge(f, t)] = res
        return weight_map
