from collections import defaultdict
from graph_tool.all import Graph

class IndexEqualityMixin(object):
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.index == other.index)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.index))

class Location(IndexEqualityMixin):
    def __init__(self, index, properties = {}):
        self.index = index
        self.properties = properties

class Configuration(IndexEqualityMixin):
    def __init__(self, index, locations, properties = {}):
        self.index = index
        self.locations = locations
        self.PEs = set()

    def add_pe(self, pe):
        self.PEs.add(pe)

class PE:
    def __init__(self, index, configuration, properties = {}):
        self.index = index
        self.properties = properties
        self.configuration = configuration
        self.type = properties.get('t', None)
        self.configuration.add_pe(self)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.index == other.index

    def __hash__(self):
        return hash((self.index))

class Accelerator:
    def __init__(self, PEs):
        self.PEs = PEs

    def get_pe(self, index):
        return next(pe for pe in self.PEs if pe.index == index)

    def configurations(self):
        return list(set([pe.configuration for pe in self.PEs]))

    def locations(self):
        locations = set()
        for config in self.configurations():
            for loc in config.locations:
                locations.add(loc)
        return locations

class Properties:
    def __init__(self, pe_properties = {}, c_properties = {}, l_properties = {}):
        self.P_p = pe_properties
        self.P_c = c_properties
        self.P_l = l_properties

class Topology:
    def __init__(self, g = None):
        self.g = g

    @classmethod
    def default_from_accelerator(cls, acc):
        g = Graph()
        g.vp["label"] = g.new_vertex_property("string");

        loc_vertices = {}
        tx_vertices = {}
        rx_vertices = {}

        # Add all location-related vertices
        for loc in acc.locations():
            # Add location vertex
            v = g.add_vertex()
            g.vp.label[v] = "Location " + str(loc.index)
            loc_vertices[loc.index] = v

            # Add receive vertex
            rx = g.add_vertex()
            g.vp.label[rx] = "rx " + str(loc.index)

            # Add transmit vertex
            tx = g.add_vertex()
            g.vp.label[tx] = "tx " + str(loc.index)

            tx_vertices[loc.index] = tx
            rx_vertices[loc.index] = rx

            # Connect the rx and tx edges
            g.add_edge(v, tx)
            g.add_edge(rx, v)

        # Add PE specific nodes
        for config in acc.configurations():
            for pe in config.PEs:
                v = g.add_vertex()
                g.vp.label[v] = "PE " + str(pe.index)

                # Wire it up to eligible locations
                for loc in config.locations:
                    assert(loc.index in tx_vertices)
                    assert(loc.index in rx_vertices)
                    rx = rx_vertices[loc.index]
                    tx = tx_vertices[loc.index]
                    g.add_edge(v, rx)
                    g.add_edge(tx, v)
        return cls(g)

class Machine:
    def __init__(self, acc, topo, properties):
        self.accelerator = acc
        self.topology = topo
        self.properties = properties

    def get_pe(self, index):
        return self.accelerator.get_pe(index)

    def PEs(self):
        return self.accelerator.PEs

    def locations(self):
        return self.accelerator.locations()
