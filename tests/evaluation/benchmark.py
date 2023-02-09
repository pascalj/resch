import unittest

from tests.context import resch
import resch.scheduling.schedule as schedule
import resch.evaluation.benchmark as bench

from tests.fixtures import fixtures

class TestBenchmark(unittest.TestCase):
    def test_machine_benchmark(self):
        M = fixtures.minimal_machine()
        Gs = [fixtures.sample_graph(), fixtures.sample_graph()]
        def algo(M, Gs):
            return fixtures.schedule_with_len(120)

        self.assertEqual(bench.machine_benchmark(M, Gs, algo).shape, (2,4))

if __name__ == '__main__':
    unittest.main()
