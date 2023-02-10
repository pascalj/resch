import unittest

from test.context import resch
import resch.scheduling.schedule as schedule
import resch.evaluation.metrics as metrics

from test.fixtures import fixtures

class TestMetrics(unittest.TestCase):
    def test_makespan_with_empty_schedule(self):
        S = fixtures.empty_schedule()
        self.assertEqual(metrics.makespan(S), 0)

    def test_makespan_with_makespan(self):
        slen = 55
        S = fixtures.schedule_with_len(slen)
        self.assertEqual(metrics.makespan(S), slen)

    def test_slr(self):
        S = fixtures.schedule_with_len(900)
        G = fixtures.sample_graph()
        self.assertEqual(metrics.slr(S, G), 3)

    def test_slack(self):
        S = fixtures.schedule_with_len(800)
        G = fixtures.sample_graph()
        self.assertIsInstance(metrics.slack(S, G), float)

    def test_cp_len_with_empty_graph(self):
        G = fixtures.empty_graph()
        self.assertEqual(metrics.cp_len(G), 0)

    def test_cp_len(self):
        G = fixtures.sample_graph()
        self.assertEqual(metrics.cp_len(G), 450)

    def test_sequential(self):
        G = fixtures.sample_graph()
        self.assertEqual(metrics.sequential(G), 2550)

    def test_speedup(self):
        S = fixtures.schedule_with_len(1000)
        G = fixtures.sample_graph()
        self.assertEqual(metrics.speedup(S, G), 2.55)

if __name__ == '__main__':
    unittest.main()
