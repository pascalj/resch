import unittest

from test.context import resch
import resch.scheduling.reft as reft
import resch.scheduling.schedule as schedule
import resch.graph.taskgraph as graph
import resch.evaluation.generator as generator

from test.fixtures import fixtures

class TestREFT(unittest.TestCase):
    def test_reft(self):
        M = fixtures.minimal_machine()
        G = fixtures.sample_graph()
        S = reft.REFT(M, G).schedule()

        with open("test_reft.csv", "w"):
            S.to_csv(file_handle)
        self.assertEqual(len(S.tasks), G.num_nodes())

    def test_reft_random(self):
        M = fixtures.minimal_machine()
        G = graph.TaskGraph(generator.random(12))
        S = reft.REFT(M, G).schedule()

        self.assertEqual(len(S.tasks), G.num_nodes())

    def test_reft_random_complex(self):
        M = fixtures.single_config_machine(num_PEs = 5, num_locs = 2)
        G = graph.TaskGraph(generator.random(25))
        S = reft.REFT(M, G).schedule()

        self.assertEqual(len(S.tasks), G.num_nodes())

    def test_reft_random_edge(self):
        M = fixtures.single_config_machine(num_PEs = 2, num_locs = 2)
        G = graph.TaskGraph(generator.random(25))
        S = reft.REFT(M, G, schedule.EdgeSchedule).schedule()

        self.assertEqual(len(S.tasks), G.num_nodes())
