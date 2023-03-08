import unittest

from test.context import resch
import resch.scheduling.reft as reft
import resch.graph.taskgraph as graph

from test.fixtures import fixtures

class TestREFT(unittest.TestCase):
    def test_reft(self):
        M = fixtures.minimal_machine()
        G = fixtures.sample_graph()
        S = reft.REFT(M, G).schedule()
