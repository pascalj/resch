from graph_tool import Graph, GraphView, generation
from graph_tool.topology import min_spanning_tree
from random import uniform, randrange
from itertools import pairwise

def erdos(n, p, cost_func = None, comcost_func = None, num_pes = 9):
    """

    Create a random graph with the Erdös-Renyi algorithm

    Args:
        n (): number of nodes
        p (): probability of to create an edge (i,j) with i<j
    """
    g = Graph()

    for _ in range(n):
        g.add_vertex()

    for i in range(n):
        for j in range(n):
            if i < j and uniform(0, 1) < p:
                e = g.add_edge(i, j)

    add_dummy_tasks(g)

    return g

def layer_by_layer(n, layers, p):
    """

    Generate a task graph with the layer-by-layer technique

    Args:
        n (): number of tasks
        layers (): number of layers
        p (): probability of an edge existing between two nodes in adjacent layers
    """

    g = Graph()

    g.vp["layer"] = g.new_vertex_property("int")

    for _ in range(n):
        v = g.add_vertex()
        g.vp["layer"][v] = randrange(layers)
   
    for (layer_p, layer_n) in pairwise(range(layers)):
        g_p = GraphView(g, vfilt=lambda v: g.vp["layer"][v] == layer_p)
        g_n = GraphView(g, vfilt=lambda v: g.vp["layer"][v] == layer_n)

        for v_p in g_p.get_vertices():
            for v_n in g_n.get_vertices():
                if uniform(0, 1) < p:
                    g.add_edge(v_p, v_n)

    add_cost(g)
    add_dummy_tasks(g)
    return g

def random(n, sampler = None):
    """

    Create a uniform random task graph

    Args:
        n (): number of tasks
        sampler (): function that returns (in_deg, out_deg) for each task

    Returns:
        
    """
    if sampler is None:
        sampler = lambda: (randrange(3), randrange(3))
    g = generation.random_graph(n, sampler)
    tree = min_spanning_tree(g)

    g.set_edge_filter(tree)

    add_cost(g)
    add_dummy_tasks(g)

    return g


def lu(num_blocks, comm_cost = None, comp_cost = None):
    """

    Generate a task graph for the blocked LU decomposition

    Args:
        num_blocks (): number of blocks in both i and j directions
        comm_cost (): lambda setting the computational cost
        comp_cost (): lambda setting the communication cost

    Returns:
        
    """
    g = Graph()
    g.vp["label"] = g.new_vertex_property("string")
    g.vp["it"] = g.new_vertex_property("int")
    g.vp["i"] = g.new_vertex_property("int")
    g.vp["j"] = g.new_vertex_property("int")
    g.vp["type"] = g.new_vertex_property("int")
    g.vp["cost"] = g.new_vertex_property("vector<int>")
    g.ep["comm"] = g.new_edge_property("int")
    tasks = {}

    if comp_cost is None:
        comp_cost = lambda it, i, j: [100]

    def gen_task(it, i, j):
        v = g.add_vertex()
        g.vp.label[v] = f'({it},{i},{j})'
        g.vp.it[v] = it 
        g.vp.i[v] = i
        g.vp.j[v] = j
        g.vp.cost[v] = comp_cost(it, i, j)
        if it == i:
            if i == j:
                g.vp.type[v] = 1 # diag
            else:
                g.vp.type[v] = 2 # col
        elif it == j:
            g.vp.type[v] = 3 # row
        else:
            g.vp.type[v] = 4 # inner
        tasks[(it, i, j)] = v
        return v

    if comm_cost is None:
        comm_cost = lambda e: 100

    def dep(v1, v2):
        e = g.add_edge(v1, v2)
        g.ep.comm[e] = comm_cost(e)

    t = lambda it, i, j: tasks[(it, i, j)]

    for it in range(num_blocks):
        # dependencies for all inner blocks
        gen_task(it, it, it)
            
        # generate row and column tasks
        for j in range(it + 1, num_blocks):
            row = gen_task(it, it, j)
            col = gen_task(it, j, it)
            dep(t(it, it, it), row)
            dep(t(it, it, it), col)

        # generate inner tasks
        for i in range(it + 1, num_blocks):
            for j in range(it + 1, num_blocks):
                inner = gen_task(it, i, j)
                dep(t(it, i, it), inner)
                dep(t(it, it, j), inner)

        # wait for all blocks to finish writing (in the previous iteration)
        if it > 0:
            for i in range(it, num_blocks):
                for j in range(it, num_blocks):
                    dep(t(it - 1, i, j), t(it, i, j))

    return g

def add_dummy_tasks(g):
    """

    Add an empty entry and exit task

    Args:
        g (): graph to change
    """
    entry_task = g.add_vertex()
    exit_task = g.add_vertex()
    g.vp.cost[entry_task] = [1] * 9
    g.vp.cost[exit_task] = [1] * 9
    for v in g.vertices():
        if v != entry_task and v != exit_task:
            entry_edge = g.add_edge(entry_task, v)
            exit_edge = g.add_edge(v, exit_task)

            g.ep.comm[entry_edge] = 1
            g.ep.comm[exit_edge] = 1

def add_cost(g, cost_func = None, comcost_func = None, num_PEs = 9):
    """

    Add computation cost and communication cost if not present

    Args:
        g (): Graph to change
        cost_func (): compute cost function (v, p) -> int
        comcost_func ():  communication cost function e -> int
        num_PEs (): how many PEs should we generator for?
    """
    if "cost" not in g.vp:
        g.vp["cost"] = g.new_vertex_property("vector<int>")
        if cost_func is None:
            cost_func = lambda v, p : 100
        for v in g.get_vertices():
            g.vp["cost"][v] = [cost_func(v, p) for p in range(num_PEs)]

    if "comm" not in g.ep:
        g.ep["comm"] = g.new_edge_property("int")
        if comcost_func is None:
            comcost_func = lambda i, j : 10
        for i, j in g.edges():
            edge = g.edge(i, j)
            g.ep["comm"][edge] = comcost_func(i, j)
