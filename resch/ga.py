import numpy as np
from geneticalgorithm import geneticalgorithm as ga
import machine, printer, graph, heft.reft
from collections import defaultdict

class GA:
    def __init__(self, g, w, c):
        self.g = g
        self.w = w
        self.c = c

    def chromosome_to_mm(self, x):
        # PE -> configuration
        rho = 20
        locs = [machine.Location(0, {'c': rho})]

        PEs = []
        for p_idx, c_idx in enumerate(x):
            config = machine.Configuration(c_idx, locs)
            properties = {'t': p_idx + 1}
            PEs.append(machine.PE(p_idx, config, properties))

        return machine.MachineModel(PEs)

    def cost(self, x):
        mm = self.chromosome_to_mm(x)
        R = heft.reft.REFT(self.g, self.w, self.c, mm)
        S = R.schedule()
        return S.length()

    def generate(self, n):
        varbound=np.array([[0,n - 1]]*n)
        algorithm_param = {'max_num_iteration': 100,\
                   'population_size':10,\
                   'mutation_probability':0.1,\
                   'elit_ratio': 0.01,\
                   'crossover_probability': 0.5,\
                   'parents_portion': 0.3,\
                   'crossover_type':'uniform',\
                   'max_iteration_without_improv':None}

        model=ga(function=self.cost,dimension=n,variable_type='int',variable_boundaries=varbound,algorithm_parameters=algorithm_param)
        
        model.run()

        return model.output_dict

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

    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w') as file:
            mm = ga.chromosome_to_mm(solution["variable"])
            S = heft.reft.build_schedule(g, w, c, mm)
            printer.save_schedule(S, file, mm)

if __name__ == '__main__':
    main()
