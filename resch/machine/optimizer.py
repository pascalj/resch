import numpy as np
from geneticalgorithm import geneticalgorithm as ga
from .. import machine, printer, graph, heft.reft
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
            'lut': 1866240,
            'ff': 3732480,
            'ram': 11721,
            'dsp': 5760,
            'c': rho
        }
        locs = [machine.Location(0, loc_properties), machine.Location(1, loc_properties)]

        PEs = []
        pe_properties = [
            {
                'lut': 334829,
                'ff': 442480,
                'ram': 1062,
                'dsp': 268,
                't': 1
            },
            {
                'lut': 334829,
                'ff': 442480,
                'ram': 1062,
                'dsp': 268,
                't': 2
            },
            {
                'lut': 334829,
                'ff': 442480,
                'ram': 1062,
                'dsp': 268,
                't': 3
            },
            {
                'lut': 158300,
                'ff': 635522,
                'ram': 7680,
                'dsp': 2148,
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
            S = R.schedule()
            print(w.mean(), S.length(), x)
            return 1.0/S.length()

        varbound = range(n)

        model = pygad.GA(num_generations = 10, num_parents_mating = 2, fitness_func=fitness, sol_per_pop=5, num_genes=n,gene_type=int, init_range_low=0, init_range_high=n-1, gene_space=varbound, save_solutions=True,parent_selection_type="rank", save_best_solutions=True)
        
        model.run()

        model.plot_fitness()
        return model.best_solutions[-1]

def usage():
    print("usage: python3 -m resch.ga <graph>.xml [solution.svg]")

def main():
    import sys

    if len(sys.argv) < 2:
        usage()
        return 1;

    (g, w, c) = graph.load(sys.argv[1])

    ga = GA(g, w, c)
    solution = ga.generate(w.shape[1])
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
