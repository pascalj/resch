from graph_tool import Graph
from random import uniform

def random(n, p, cost_func = None, comcost_func = None, num_pes = 9):
    """

    Create a random graph with the Erdös-Renyi algorithm

    Args:
        n (): number of nodes
        p (): probability of to create an edge (i,j) with i<j
    """
    g = Graph()

    cost = g.new_vertex_property("vector<int>")
    comm = g.new_edge_property("int")

    # Add a dummy entry and a dummy exit task
    
    if cost_func is None:
        cost_func = lambda v, p : 100
    if comcost_func is None:
        comcost_func = lambda i, j : 100

    for _ in range(n):
        v = g.add_vertex()
        cost[v] = [cost_func(v, p) for p in range(num_pes)]

    for i in range(n):
        for j in range(n):
            if i < j and uniform(0, 1) < p:
                e = g.add_edge(i, j)
                comm[e] = comcost_func(i, j)

    entry_task = g.add_vertex()
    exit_task = g.add_vertex()
    for v in g.vertices():
        g.add_edge(entry_task, v)
        g.add_edge(v, exit_task)

    return g

def simple_graph(num_pes = 2, num_locs = 1):
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

def lu_graph(num_blocks):
    g = gt.Graph()
    g.vp["label"] = g.new_vertex_property("string")
    g.vp["it"] = g.new_vertex_property("int")
    g.vp["i"] = g.new_vertex_property("int")
    g.vp["j"] = g.new_vertex_property("int")
    g.vp["type"] = g.new_vertex_property("int16_t")
    g.vp["cost"] = g.new_vertex_property("vector<int>")
    g.ep["comm"] = g.new_edge_property("vector<int>")
    tasks = {}
    
    def gen_task(it, i, j):
        v = g.add_vertex()
        g.vp.label[v] = f'({it},{i},{j})'
        g.vp.it[v] = it 
        g.vp.i[v] = i
        g.vp.j[v] = j
        g.vp.cost[v] = [80, 60, 100, 100]
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

    def dep(v1, v2):
        e = g.add_edge(v1, v2)
        g.ep.comm[e] = [0, 10, 10, 0]

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
