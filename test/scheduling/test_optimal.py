import unittest

from test.context import resch
import resch.scheduling.optimal as optimal
import resch.scheduling.schedule as schedule
import resch.graph.taskgraph as graph
import resch.evaluation.generator as generator

from test.fixtures import fixtures

class TestOptimal(unittest.TestCase):
    def test_optimal(self):
        M = fixtures.single_config_machine(num_PEs = 2, num_locs = 1)
        G = graph.TaskGraph(generator.random(10))
        S = optimal.OptimalScheduler(M, G).schedule()

        self.assertEqual(len(S.tasks), G.num_nodes())
