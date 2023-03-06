import unittest

from test.context import resch
import resch.evaluation.generator as generator

from test.fixtures import fixtures
from graph_tool.all import graph_draw

class TestGenerator(unittest.TestCase):
    def test_random(self):
        n = 25 
        g = generator.random(n, 0.2)
        graph_draw(g, output="test.pdf")
        self.assertEqual(g.num_vertices(), n + 2)
