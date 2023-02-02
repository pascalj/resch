import unittest

from .context import resch
import resch.scheduling.schedule as schedule
import resch.metrics as metrics

class TestMetrics(unittest.TestCase):
    def test_makespan_with_empty_schedule(self):
        S = schedule.Schedule()
        self.assertEqual(metrics.makespan(S), 0)

if __name__ == '__main__':
    unittest.main()
