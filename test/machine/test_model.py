import unittest

from test.context import resch
import resch.machine.model as model
from resch.machine.model import Location, Configuration, PE, Machine, Accelerator, Topology

from test.fixtures import fixtures
from graph_tool.all import graphviz_draw

class TestModel(unittest.TestCase):
    def test_default_topo(self):
        locations = [Location(0), Location(1)]
        configurations = [Configuration(0, locations), Configuration(1, [locations[1]])]
        PEs = [PE(0, configurations[0]), PE(1, configurations[0]), PE(2, configurations[1])]
        acc = Accelerator(PEs)

        topo = Topology.default_from_accelerator(acc)
        graphviz_draw(topo.g, layout="dot", vprops={"label": topo.g.vp.label})
        self.assertEqual(topo.g.num_vertices(), 9)
        self.assertEqual(topo.g.num_edges(), 14)
