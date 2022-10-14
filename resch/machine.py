from collections import defaultdict

class IndexEqualityMixin(object):
    def __eq__(self, other):
        return (isinstance(other, self.__class__)
            and self.index == other.index)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash((self.index))

class Location(IndexEqualityMixin):
    def __init__(self, index):
        self.index = index

class Configuration(IndexEqualityMixin):
    def __init__(self, index, locations):
        self.index = index
        self.locations = locations
        self.PEs = set()

    def add_pe(self, pe):
        self.PEs.add(pe)

class Property:
    name = "uninitialized"
    value = False

class PE:
    def __init__(self, index, configuration, properties):
        self.index = index
        self.properties = properties
        self.configuration = configuration
        self.type = properties.get('p_ft', None)
        self.configuration.add_pe(self)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.index == other.index

    def __hash__(self):
        return hash((self.index))

class MachineModel:
    def __init__(self, PEs):
        self.PEs = PEs

    def get_pe(self, index):
        return next(pe for pe in self.PEs if pe.index == index)

    def configurations(self):
        return list(set([pe.configuration for pe in self.PEs]))

def get_pr(num_PEs, num_slots):
    locations = [Location(l_id) for l_id in range(num_slots)]
    PEs = []
    for pe_id in range(num_PEs):
        config = Configuration(pe_id, locations)
        PEs.append(PE(pe_id, config, {}))
    return MachineModel(PEs)

# Get a non-PR machine with a mapping of config_to_PEs
def get_r(config_to_PEs):
    locations = [Location(0), Location(1)]
    PEs = []
    for config, pes in enumerate(config_to_PEs):
        config = Configuration(config, locations)
        for pe in pes:
            properties = {'p_ft': [pe + 1, pe + 2]}
            PEs.append(PE(pe, config, properties))
    return MachineModel(PEs)
