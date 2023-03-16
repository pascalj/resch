from collections import defaultdict
from graph_tool.all import Graph, GraphView
from graph_tool.topology import shortest_path
from graph_tool.util import find_vertex
from graph_tool.draw import graphviz_draw

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

    def __get__item(self, key):
        if type(key) == PE:
            assert(key in self.P_p)
            return self.P_p[key]
        if type(key) == Configuration:
            assert(key in self.P_c)
            return self.P_c[key]
        if type(key) == Location:
            assert(key in self.P_l)
            return self.P_l[key]
        assert(False)


class Topology:
    def __init__(self, g = None, PE_map = {}):
        self.g = g
        self.PE_g = GraphView(g, vfilt=self.g.vp.is_PE)
        self.PE_map = PE_map

    @classmethod
    def default_from_accelerator(cls, acc):
        g = Graph()
        g.vp["label"] = g.new_vertex_property("string");
        g.vp["PE"] = g.new_vertex_property("int");
        g.vp["is_PE"] = g.new_vertex_property("bool");
        g.vp["location"] = g.new_vertex_property("int");

        g.ep["capacity"] = g.new_edge_property("float");

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
            rx_edge = g.add_edge(rx, v)
            tx_edge = g.add_edge(v, tx)

            g.ep.capacity[rx_edge] = 1
            g.ep.capacity[tx_edge] = 1

        locs = list(acc.locations())
        for lhs, rhs in zip(locs, locs[1:]):
            lhs_loc = loc_vertices[lhs.index]
            rhs_loc = loc_vertices[rhs.index]

            rx_edge = g.add_edge(lhs_loc, rhs_loc)
            tx_edge = g.add_edge(rhs_loc, lhs_loc)

            g.ep.capacity[rx_edge] = 1
            g.ep.capacity[tx_edge] = 1

        PE_map = {}
        # Add PE specific nodes
        for config in acc.configurations():
            for pe in config.PEs:

                # Wire it up to eligible locations
                for loc in config.locations:
                    v = g.add_vertex()
                    g.vp.label[v] = f"PE {pe.index}@{loc.index}"
                    g.vp.PE[v] = pe.index
                    g.vp.is_PE[v] = True
                    g.vp.location[v] = loc.index
                    PE_map[(pe.index, loc.index)] = v

                    assert(loc.index in tx_vertices)
                    assert(loc.index in rx_vertices)
                    rx = rx_vertices[loc.index]
                    tx = tx_vertices[loc.index]
                    rx_edge = g.add_edge(v, rx)
                    tx_edge =g.add_edge(tx, v)

                    g.ep.capacity[rx_edge] = 1
                    g.ep.capacity[tx_edge] = 1

        return cls(g, PE_map = PE_map)

    def path(self, src, dst):
        """

        Get the shortest path (edges) from a node to another

        Args:
            from (): Vertex
            to (): Vertex

        Returns: [Edge]
            
        """
        (vertices, edges) = shortest_path(self.g, src, dst)
        return edges

    def pe_path(self, src_placed, dst_placed):
        assert(src_placed in self.PE_map)
        assert(dst_placed in self.PE_map);

        src_node = self.PE_map[src_placed] 
        dst_node = self.PE_map[dst_placed] 
        path = self.path(src_node, dst_node)

        assert(src_placed == dst_placed or src_node != dst_node)
        assert(src_placed == dst_placed or len(path) > 0)

        return path


    def relative_capacity(self, link):
        """
        Get the relative capacity from 0 < c <= 1

        Args:
            link (): the edge in the topology
        """
        return self.g.ep.capacity[link]

    def show(self):
        graphviz_draw(self.g, layout="dot")


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
