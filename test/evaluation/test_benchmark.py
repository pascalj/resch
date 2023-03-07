import unittest

from test.context import resch
import resch.scheduling.schedule as schedule
import resch.evaluation.benchmark as bench
import resch.evaluation.generator as generator
import resch.graph.taskgraph as graph

from test.fixtures import fixtures

class TestBenchmark(unittest.TestCase):
    def test_machine_benchmark(self):
        M = fixtures.minimal_machine()
        random = graph.TaskGraph(generator.random(10))
        random.set_uniform_cost(100).set_uniform_comm(50)
        Gs = [fixtures.sample_graph(), fixtures.sample_graph(), random]
        def algo(M, Gs):
            return fixtures.schedule_with_len(120)

        self.assertEqual(bench.machine_benchmark(M, Gs, algo).shape, (3,4))

if __name__ == '__main__':
    unittest.main()
