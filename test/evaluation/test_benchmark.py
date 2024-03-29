import unittest

from test.context import resch
import resch.scheduling.schedule as schedule
import resch.evaluation.benchmark as bench
import resch.evaluation.generator as generator
import resch.graph.taskgraph as graph
import resch.scheduling.reft as reft

from test.fixtures import fixtures

class TestBenchmark(unittest.TestCase):
    def test_machine_benchmark(self):
        M = fixtures.minimal_machine()
        random = graph.TaskGraph(generator.random(10))
        random.set_uniform_cost(100).set_uniform_comm(50)
        Gs = [fixtures.sample_graph(), fixtures.sample_graph(), random]
        def algo(M, G):
            return reft.REFT(M, G).schedule()

        results = bench.machine_benchmark(M, Gs, algo, {})

        self.assertEqual(results.shape, (3, 10))

if __name__ == '__main__':
    unittest.main()
