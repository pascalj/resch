import unittest

from test.context import resch
import resch.evaluation.generator as generator

from test.fixtures import fixtures
from graph_tool.all import graphviz_draw

class TestGenerator(unittest.TestCase):
    def test_erdos(self):
        n = 25
        p = 0.2
        g = generator.erdos(n, p)
        # Need entry and exit-node
        self.assertEqual(g.num_vertices(), n + 2)

    def test_layer_by_layer(self):
        n = 25
        layers = 3
        p = 0.2
        g = generator.layer_by_layer(n, layers, p)

        self.assertEqual(g.num_vertices(), n + 2)

    def test_random(self):
        n = 25
        g = generator.random(n)
        # Need entry and exit-node
        self.assertEqual(g.num_vertices(), n + 2)

    def test_lu(self):
        blocks = 5
        g = generator.lu(blocks)
        # Need entry and exit-node
        self.assertEqual(g.num_vertices(), 55)
