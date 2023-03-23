import unittest

from test.context import resch
import resch.scheduling.optimal as optimal
import resch.scheduling.schedule as schedule
import resch.machine.model as model
import resch.graph.taskgraph as graph
import resch.evaluation.generator as generator

from test.fixtures import fixtures

class TestOptimal(unittest.TestCase):
    def test_optimal(self):
        M = fixtures.single_config_machine(num_PEs = 2, num_locs = 1)
        G = graph.TaskGraph(generator.random(10))
        (S, E) = optimal.OptimalScheduler(M, G).schedule()


        self.assertEqual(len(S.tasks), G.num_nodes())

    def test_optimal_edge(self):
        M = fixtures.single_config_machine(num_PEs = 2, num_locs = 2)
        M.topology = model.Topology.default_from_accelerator(M.accelerator)
        G = graph.TaskGraph(generator.random(10))
        (S, E) = optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()

        self.assertEqual(len(S.tasks), G.num_nodes())

    def test_optimal_multi(self):
        M = fixtures.pr_machine(num_PEs = 2, num_locs = 2)
        M.topology = model.Topology.default_from_accelerator(M.accelerator)
        G = graph.TaskGraph(generator.random(5))
        (S, E) = optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()

        self.assertEqual(len(S.tasks), G.num_nodes())

    def test_optimal_multi_reconf(self):
        M = fixtures.pr_machine(num_PEs = 2, num_locs = 2)
        for l in M.locations():
            M.properties[l]["r"] = 50 

        M.topology = model.Topology.default_from_accelerator(M.accelerator)
        G = graph.TaskGraph(generator.random(5))
        (S, E) = optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()

        self.assertEqual(len(S.tasks), G.num_nodes())
