import unittest

from test.context import resch
import resch.machine.model as model

from test.fixtures import fixtures
from graph_tool.all import graphviz_draw

class TestOptimizer(unittest.TestCase):
    def test_interface(self):

