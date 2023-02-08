from graph_tool import load_graph
from graph_tool import topology, draw
from math import sqrt
from resch import graph
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

    return graph.TaskGraph(g)

def save(g, file):
    makedirs(dirname(file), exist_ok = True)
    g.save(file, fmt="graphml")

def save_pdf(g, file):
    vpr = {"label": g.vp.label}
    draw.graphviz_draw(g, vcolor=g.vp.type, vcmap=mpl.colormaps['Pastel1'], layout="dot", output="reft.pdf", vnorm=0,vprops=vpr)
