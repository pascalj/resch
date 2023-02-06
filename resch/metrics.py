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
    S

    return makespan(S) / cp_len(G)

""" Length of the critical Path of G

G : (g, w, c, t)
"""

def cp_len(G):

    return G.cp_len()
