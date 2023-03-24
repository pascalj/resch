import unittest

from test.context import resch
import resch.machine.model as model
from resch.machine.model import Location, Configuration, PE, Machine, Accelerator, Topology

from test.fixtures import fixtures

class TestModel(unittest.TestCase):
    def test_default_topo(self):
        locations = [Location(0), Location(1)]
        configurations = [Configuration(0, locations), Configuration(1, [locations[1]])]
        PEs = [PE(0, configurations[0]), PE(1, configurations[0]), PE(2, configurations[1])]
        acc = Accelerator(PEs)

        topo = Topology.default_from_accelerator(acc)
        self.assertEqual(topo.g.num_vertices(), 11) # 2 x 2 locations, 1 x 1 location, 2 x tx, 2 x rx, 2 x loc
        self.assertEqual(topo.g.num_edges(), 16)
