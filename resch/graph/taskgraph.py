class TaskGraph:
    def __init__(self, g):
        (g, w, c, t) = self.from_graph(g)
        self.g = g
        self.w = w
        self.c = c
        self.t = t

    def from_graph(self, g):
        cost = g.vp['cost']
        t = g.vp['type']
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

    def cp_len(self):
        if self.g.vertex_count() == 0:
            return 0;

        w_bar = self.w.mean(axis=1)
        c_bar = self.c.mean(axis=[2,3])
        sort = gt.topological_sort(g)

        first = g[sort[0]]
        last = g[sort[1]]

        # Accumulated cost (source node weight + edge weight)
        weight_map = g.new_edge_property("acc_cost", numpy.inf)
        for v, v_idx in g.iter_vertices([g.vertex_index]):
           for e, e_idx, cost in g.iter_out_edges(v, [g.edge_index, g.ep['comm']):
               map[e_idx] = w_bar[v_idx] + c_bar[e_idx]

        (dist_map) = gt.shortest_distance(g, source=first, target=last, weights=weight_map)
        
        return dist_map[first]
