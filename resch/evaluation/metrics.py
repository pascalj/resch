""" Simple schedule length

S : Schedule
"""

def makespan(S):
    return S.length()

""" Schedule length ratio

s : Schedule
G : TaskGraph
"""

def slr(S, G):
    return makespan(S) / sum(G.min_p(v)[1] for (v, e) in G.cp())

def slack(S, G):
    slen = makespan(S)
    return sum(slen - G.rank_u(v) - G.rank_d(v) for v in G.nodes()) / G.num_nodes()

""" Length of the critical Path of G

G : (g, w, c, t)
"""

def cp_len(G):
    return G.cp_len()

