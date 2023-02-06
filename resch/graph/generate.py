from graph_tool import Graph

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

def generate_lu(num_blocks):
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