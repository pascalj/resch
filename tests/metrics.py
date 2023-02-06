import unittest

from .context import resch
import resch.scheduling.schedule as schedule
import resch.metrics as metrics

from .fixtures import fixtures

class TestMetrics(unittest.TestCase):
    def test_makespan_with_empty_schedule(self):
        S = fixtures.empty_schedule()
        self.assertEqual(metrics.makespan(S), 0)

    def test_makespan_with_makespan(self):
        slen = 55
        S = fixtures.schedule_with_len(slen)
        self.assertEqual(metrics.makespan(S), slen)

    def test_cp_len_with_empty_graph(self):
        G = fixtures.empty_graph()
        self.assertEqual(metrics.cp_len(G), 0)

    def test_cp_len(self):
        G = fixtures.sample_graph()
        self.assertEqual(metrics.cp_len(G), 55)

if __name__ == '__main__':
    unittest.main()
