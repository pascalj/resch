import numpy as np
# from .. import machine, printer, graph, schedule
from resch import machine, graph, scheduling, evaluation
from resch.evaluation import generator
from resch.scheduling import schedule
from collections import defaultdict
import copy
import pygad

class GA:
    def __init__(self, g, chromosome_to_mm):
        self.g = g
        self.chromosome_to_mm = chromosome_to_mm
        self.resource_properties = ["lut", "ff", "ram", "dsp"]

    def apply_cong(self, mm, g):
        P_c = {}

        def h_linear(x, a, b):
            if x <= a:
                return 0
            if a < x < b:
                return (x-a)/(b-a)
            return 1

        for c in mm.configurations():
            for prop in self.resource_properties: 
                P_c[prop] = sum(mm.properties[pe].get(prop, 0) for pe in c.PEs)
            x = h_linear(max(sum(P_c[prop] / mm.properties[l].get(prop, 1) for l in mm.locations()) / len(mm.locations()) for prop in self.resource_properties), 0.7, 1)

            for pe in c.PEs:
                g.w[:,pe.original_index] = g.w[:,pe.original_index] / (1.00001 - x)

    def apply_optimizations(self, mm, g):
        for c in mm.configurations():
            for pe in c.PEs:
                g.w[:,pe.original_index] = g.w[:,pe.original_index] / mm.properties[pe]["factor"]

    def generate(self, gene_space, num_configurations = 2, n = 4, k = 1, solutions = [], fitnesses = []):

        # TODO: cleanup
        solutions_d = []
        def fitness(ga_instance, solution, solution_index):
            mm = self.chromosome_to_mm(solution)
            g = copy.deepcopy(self.g)
            self.apply_cong(mm, g)
            self.apply_optimizations(mm, g)

            R = scheduling.reft.REFT(mm, g, schedule.NoEdgeSchedule)
            (S, E) = R.schedule()
            print(S.length(), solution)

            fit = 1.0/S.length()

            solutions_d.append((ga_instance.generations_completed, solution, k, S, E))
            return fit


        model = pygad.GA(num_generations = 100, num_parents_mating = 2, fitness_func=fitness, sol_per_pop=10, num_genes=n,gene_type=int, init_range_low=0, init_range_high=n-1, gene_space=gene_space, save_solutions=True,parent_selection_type="rank", save_best_solutions=True, suppress_warnings=True)
        
        model.run()

        best_solution, best_solution_fitness, best_solution_index = model.best_solution()
        print(f"best solution: {best_solution}, best_solution_fitness: {1/best_solution_fitness}, index: {best_solution_index}")
        # model.plot_fitness()

        solutions.extend(model.solutions)
        fitnesses.extend(model.solutions_fitness)

        return solutions_d

def main():
    import sys

    g = graph.taskgraph.TaskGraph(generator.lu(8))
    ga = GA(g)
    solution = ga.generate()

    if len(sys.argv) > 2:
        with open(sys.argv[2], 'w') as file:
            mm = ga.chromosome_to_mm(solution)
            w = ga.apply_cong(mm)
            (S, E) = scheduling.reft.REFT(g, mm).schedule()
            printer.save_schedule(S, file, mm)

if __name__ == '__main__':
    main()
