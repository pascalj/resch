from graph_tool import load_graph, Graph
from graph_tool import topology, draw
from task import Task
from math import sqrt
import matplotlib as mpl
import numpy as np
from os.path import dirname
from os import makedirs

def import_dot(file):
    return gt.load_graph(file, fmt="dot")

def load(file):
    """Returns a (g, w, c, t) for a given graph file in GraphML"""
    g = load_graph(file)

    g.gp["title"] = g.new_gp("string")
    g.gp["title"] = file

    cost = g.vp['cost']
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

        

    return (g, w, c)


def save(g, file):
    makedirs(dirname(file), exist_ok = True)
    g.save(file, fmt="graphml")

def save_pdf(g, file):
    vpr = {"label": g.vp.label}
    draw.graphviz_draw(g, vcolor=g.vp.type, vcmap=mpl.colormaps['Pastel1'], layout="dot", output="reft.pdf", vnorm=0,vprops=vpr)
