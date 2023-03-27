import numpy as np
import pdb
from math import sqrt
from graph_tool.topology import topological_sort, shortest_path
from functools import cache
from resch.scheduling import task
 
class TaskGraph:
    def __init__(self, g):
        (g, w, c, t) = self.from_graph(g)
        self.g = g
        self.w = w
        self.c = c
        self.t = t
        self.w_bar = self.w.mean(axis=1)
        self.c_bar = self.c
        self.w_min = np.argmin(self.w, axis=1)
        self.init_maps()

    def init_maps(self):
        self.g.vp["rank_u"] = self.g.new_vertex_property('int')
        self.g.vp["rank_d"] = self.g.new_vertex_property('int')

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
            c = np.zeros((g.num_vertices(), g.num_vertices()))
            for s, d, edge_cost in g.iter_edges([com_cost]):
                c[s, d] = edge_cost
        else:
            c = np.zeros((g.num_vertices(), g.num_vertices()))
        return (g, w, c, t)

    def nodes(self):
        """ Array of nodes """
        return self.g.get_vertices()

    def num_nodes(self):
        """ Number of total nodes """
        return self.g.num_vertices()

    def num_edges(self):
        return self.g.num_edges()

    def path_len(self, path, weights=None):
        """ Path length with w """

        if weights is None:
            weights = self.inclusive_cost_map()
        return sum(weights[e] for e in path)

    def min_p(self, v):
        """ Returns the index of the PE that has the minimal execution cost and its value """

        v = self.g.vertex_index[v]
        return (self.w_min[v], self.w[v, self.w_min[v]])

    def cp_len(self, weights=None):
        """ Length of the critical path in terms of w and c """

        g = self.g
        if g.num_vertices() == 0:
            return 0;

        if weights is None:
            weights = self.inclusive_cost_map()

        return self.path_len(self.cp(weights=weights), weights=weights)

    def set_task_type(self, task, type):
        self.t[task.index] = type

    def cp(self, weights=None):
        """ Returns the edge list of the critical path """
        first = self.entry_node()
        last = self.exit_node()

        if weights is None:
            weights = self.inclusive_cost_map()

        nodes, edges = shortest_path(self.g, source=self.entry_node(), target=self.exit_node(), weights=weights)

        return edges


    def entry_node(self):
        """ The entry node (a node without in dependencies) """
        sort = self.sorted_topologically()
        return self.g.vertex(sort[0])

    def exit_node(self):
        """ The exit node (a node without out dependencies) """
        sort = self.sorted_topologically()
        return self.g.vertex(sort[-1])

    def sorted_topologically(self):
        return topological_sort(self.g)

    def sorted_by_urank(self):
        sorted_ids = sorted(self.g.get_vertices(), key = lambda v: -(self.rank_u(v)))
        return [self.task(id) for id in sorted_ids]

    def task(self, node_id):
        label = f"Task {node_id}"
        if "label" in self.g.vp:
            label = self.g.vp.label[node_id]
        cost = self.w[node_id]
        if self.t[node_id]:
            ttype = self.t[node_id]
        else:
            ttype = None
        return task.Task(node_id, label, cost, ttype)

    def tasks(self):
        return [self.task(v) for v in self.g.get_vertices()]

    def dependencies(self, task):
        return self.g.vertex(task.index).in_neighbors()

    def task_dependencies(self, task):
        return [self.task(int(v)) for v in self.g.vertex(task.index).in_neighbors()]

    def inclusive_cost_map(self):
        """ Returns an edge property map with computing cost included

            The cost are calculated based on w_bar and c_bar. The cost for each
            edge (f, t) is w_bar(f) + c_bar(f, t).
        """

        # Accumulated cost (source node weight + edge weight)
        g = self.g
        if "inclusive_cost" not in g.ep:
            weight_map = g.new_edge_property("int32_t", np.iinfo(np.int32).max)
            for v, v_idx in g.iter_vertices([g.vertex_index]):
               for f, t, e_idx, cost in g.iter_out_edges(v, [g.edge_index, g.ep['comm']]):
                   res = self.w_bar[v_idx] + self.c[f][t]
                   weight_map[g.edge(f, t)] = res
            g.ep["inclusive_cost"] = weight_map

        return g.ep["inclusive_cost"]

    def task_cost(self, task, pe):
        return self.g.vp.cost[task.index][pe.index]

    def edge(self, src_task, dst_task):
        return self.g.edge(src_task.index, dst_task.index)

    def edge_cost(self, src_task, dst_task):
        edge = self.g.edge(src_task.index, dst_task.index)
        assert(edge is not None)
        return self.g.ep.comm[edge]

    def set_uniform_cost(self, cost):
        if "cost" not in self.g.vp:
            self.g.vp["cost"] = self.g.new_vertex_property("vector<int>");
        for v in self.g.get_vertices():
            self.g.vp.cost[v] = [cost]
            self.w[v][0] = cost
            self.w_bar[v] = cost
        return self

    def set_uniform_comm(self, comm_cost):
        if "comm" not in self.g.ep:
            self.g.ep["comm"] = self.g.new_edge_property("int");
        for e in self.g.edges():
            self.g.ep.comm[e] = comm_cost
            (src, tgt) = e
            
            self.c[int(src), int(tgt)] = comm_cost
            self.c_bar[int(src), int(tgt)] = comm_cost
        return self

    def show(self):
        pass


    @cache
    def rank_u(self, v):
        """ Get the upper rank of node v """
        value = self.w_bar[v] + max(
                [self.c_bar[v][w] + self.rank_u(w) for w in self.g.get_out_neighbors(v)],
                default=0)
        self.g.vp['rank_u'][v] = value
        return value

    @cache
    def rank_d(self, v):
        """ Get the downwards rank of node v """
        value = max(
                    [self.rank_d(w) + self.w_bar[w] + self.c_bar[v][w] for w in self.g.get_in_neighbors(v)],
                    default=0)
        self.g.vp['rank_d'][v] = value
        return value

