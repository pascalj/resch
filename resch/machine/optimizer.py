import numpy as np
# from .. import machine, printer, graph, schedule
from resch import machine, graph
from collections import defaultdict
import pygad

class GA:
    def __init__(self, g, w, c):
        self.g = g
        self.w = w
        self.c = c
        self.resource_properties = ["lut", "ff", "ram", "dsp"]

    def chromosome_to_mm(self, x):
        # PE -> configuration
        rho = 20
        loc_properties = {
            'lut': 1866240 - 100000,
            'ff': 3732480 - 275150,
            'ram': 11721 - 467,
            'dsp': 5760 - 0,
            'c': rho
        }
        locs = [machine.Location(0, loc_properties)]

        PEs = []
        pe_properties = [
            {
                'lut': 10421,
                'ff': 25554,
                'ram': 174,
                'dsp': 6,
                't': 1
            },
            {
                'lut': 10667,
                'ff': 26992,
                'ram': 154,
                'dsp': 6,
                't': 2
            },
            {
                'lut': 5454,
                'ff': 12976,
                'ram': 83,
                'dsp': 4,
                't': 3
            },
            {
                'lut': 5454,
                'ff': 13169,
                'ram': 80,
                'dsp': 4,
                't': 4
            }
        ]
        configs = {}
        for c_idx in set(x):
            configs[c_idx] = machine.Configuration(c_idx, locs)
        for p_idx, c_idx in enumerate(x):
            config = configs[c_idx]
            PEs.append(machine.PE(p_idx, config, pe_properties[p_idx]))

        return machine.MachineModel(PEs)

    def apply_cong(self, mm):
        P_c = {}
        w = self.w.copy()

        def h_linear(x, a, b):
            if x <= a:
                return 0
            if a < x < b:
                return (x-a)/(b-a)
            return 1

        # TODO: add h!!!!
        for c in mm.configurations():
            for prop in self.resource_properties: 
                P_c[prop] = sum(pe.properties.get(prop, 0) for pe in c.PEs)

            x = h_linear(max(sum(P_c[prop] / l.properties.get(prop) for l in mm.locations()) / len(mm.locations()) for prop in self.resource_properties), 0.7, 1)

            for pe in c.PEs:
                w[:,pe.index] = self.w[:,pe.index] / (1 - x)
        return w


    def generate(self, n):
        # TODO: cleanup
        def fitness(x, idx):
            mm = self.chromosome_to_mm(x)
            w = self.apply_cong(mm)
            R = heft.reft.REFT(self.g, w, self.c, mm)
            (S, E) = R.schedule()
            print(w.mean(), S.length(), x)
            return 1.0/S.length()

        varbound = range(n)

        model = pygad.GA(num_generations = 10, num_parents_mating = 2, fitness_func=fitness, sol_per_pop=5, num_genes=n,gene_type=int, init_range_low=0, init_range_high=n-1, gene_space=varbound, save_solutions=True,parent_selection_type="rank", save_best_solutions=True)
        
        model.run()

        model.plot_fitness()
        return model.best_solutions[-1]

def main():
    import sys

    if len(sys.argv) < 2:
        return 1;

    g = graph.load(sys.argv[1])

    print(g)

    ga = GA(g, g.w, g.c)
    solution = ga.generate(g.w.shape[1])
    print(solution)

    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w') as file:
            mm = ga.chromosome_to_mm(solution)
            w = ga.apply_cong(mm)
            print(w.mean())
            S = heft.reft.build_schedule(g, w, c, mm)
            printer.save_schedule(S, file, mm)

if __name__ == '__main__':
    main()
