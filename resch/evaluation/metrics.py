def makespan(S):
    """ Simple schedule length

    S : Schedule
    """

    return S.length()

def speedup(S, G):
    """ Speedup over sequential execution

    Args:
        S (): Schedule
        G (): TaskGraph

    Returns:
        
    """
    return sequential(G) / makespan(S)


def slr(S, G):
    """ Schedule length ratio

    s : Schedule
    G : TaskGraph
    """
    return makespan(S) / sum(G.min_p(v)[1] for (v, e) in G.cp())

def slack(S, G):
    """ Calculate the slack

    Args:
        S (): Schedule
        G (): TaskGraph

    Returns:
        double: the slack
        
    """
    slen = makespan(S)
    return sum(slen - G.rank_u(v) - G.rank_d(v) for v in G.nodes()) / G.num_nodes()

def efficiency_r(S, G, m, c, r):
    s = speedup(S, G)
    available_resource = m.properties[m][r]
    used_resources = sum([m.properties[pe][r] for pe in c.PEs])
    return s / (used_resources / available_resource)

def efficiency(S, G, m):
    s = speedup(S, G)
    resources = ["lut", "ff", "ram", "dsp"]
    return min(efficiency_r(S, G, m, c, r) for r in resources for c in m.configurations())


def cp_len(G):
    """ Length of the critical Path of G

    G : (g, w, c, t)
    """

    return G.cp_len()

def sequential(G):
    """ Sequential execution time based on w_bar

    Args:
        G (): TaskGraph

    Returns:
        int: the duration
    """
    return sum(G.w_bar[v] for v in G.nodes())
