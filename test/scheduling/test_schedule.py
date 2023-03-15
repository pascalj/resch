import unittest

from test.context import resch
import resch.scheduling.schedule as schedule
from test.fixtures import fixtures
from io import StringIO

class TestREFT(unittest.TestCase):
    def test_reft(self):
        S = fixtures.schedule_with_len(500)

        output = StringIO()
        S.to_csv(output)
        output.seek(0)
        lines = output.readlines()

        self.assertEqual(len(lines), 2)
