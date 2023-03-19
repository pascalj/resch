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
        M = fixtures.single_config_machine(num_PEs = 2, num_locs = 1)
        M.topology = model.Topology.default_from_accelerator(M.accelerator)
        G = graph.TaskGraph(generator.random(10))
        (S, E) = optimal.OptimalScheduler(M, G, schedule.EdgeSchedule).schedule()

        with open("test_optimal.csv", "w") as f:
            S.to_csv(f)

        with open("test_optimal_edge.csv", "w") as f:
            E.to_csv(f)

            # Todo: find out why there are paths with 2 links

        self.assertEqual(len(S.tasks), G.num_nodes())

