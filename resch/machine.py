from collections import defaultdict

class Location:
    def __init__(self, index):
        self.index = index


class Configuration:
    def __init__(self, index, locations):
        self.index = index
        self.locations = locations

class Property:
    name = "uninitialized"
    value = False

class PE:
    def __init__(self, index, configuration, properties):
        self.index = index
        self.properties = properties
        self.configuration = configuration

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
        PEs.append(PE(pe_id, config, []))
    return MachineModel(PEs)

def get_r(config_to_PEs):
    locations = [Location(0)]
    PEs = []
    for config, pes in enumerate(config_to_PEs):
        config = Configuration(config, locations)
        for pe in pes:
            properties = {'p_ft': pe / 2}
            PEs.append(PE(pe, config, properties))
    return MachineModel(PEs)
