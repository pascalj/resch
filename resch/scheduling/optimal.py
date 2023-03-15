import collections
from ortools.sat.python import cp_model

import resch.scheduling.schedule as schedule
import resch.scheduling.task as task
import portion as po


# Takes a graph and machine models and gets the optimal schedule
class OptimalScheduler:
    def __init__(self, M, G):
        self.M = M
        self.G = G

    def schedule(self):
        self.model = cp_model.CpModel()
        M = self.M
        G = self.G
        model = self.model

        InstanceVar = collections.namedtuple("Instance", "t_s cost t_f active interval pe location task")
                                                                     # ^ only for NewOptionalIntervalVar

        horizon = 5000
        instances = {}
        config_active = {}

        tasks = [G.task(v) for v in G.sorted_topologically()]
        for task in tasks:
            for pe in M.PEs():
                for l in M.locations():
                    suffix = f"_{task.index}_{pe.index}_{l.index}"
                    active = model.NewBoolVar(f"active{suffix}")
                    t_s = model.NewIntVar(0, horizon, f"t_s{suffix}")
                    cost = G.task_cost(task, pe)
                    cost = model.NewIntVar(cost, cost, f"t_f{suffix}")
                    t_f = model.NewIntVar(0, horizon, f"t_f{suffix}")
                    interval = model.NewOptionalIntervalVar(t_s, cost, t_f, active, "active")
                    instances[(pe.index, l.index, task.index)] = InstanceVar(active=active, t_s=t_s, cost=cost, t_f=t_f, interval=interval, pe=pe, location=l, task=task)

        # Execute each task on exactly one placed PE
        for task in tasks:
            for l in M.locations():
                model.AddExactlyOne(instances[(pe.index, l.index, task.index)].active for pe in M.PEs())

        for task in tasks:
            for dependency in G.task_dependencies(task):
                for src_pe in M.PEs():
                    for src_l in M.locations():
                        for dst_pe in M.PEs():
                            for dst_l in M.locations():
                                model.Add(instances[(src_pe.index, src_l.index, dependency.index)].t_f < instances[(dst_pe.index, dst_l.index, task.index)].t_s)
        # No overlap
        for pe in M.PEs():
            for l in M.locations():
                model.AddNoOverlap(instances[(pe.index, l.index, task.index)].interval for task in tasks)

        obj_var = model.NewIntVar(0, horizon, 'makespan')
        model.AddMaxEquality(obj_var, [i.t_f for k, i in instances.items()])
        model.Minimize(obj_var)

        solver = cp_model.CpSolver()
        schedule_builder = ScheduleBuilder(G, M, instances)

        solver.Solve(model, schedule_builder)
        print('\nStatistics')
        print('  - conflicts      : %i' % solver.NumConflicts())
        print('  - branches       : %i' % solver.NumBranches())
        print('  - wall time      : %f s' % solver.WallTime())
        print('  - solutions found: %i' % schedule_builder.solution_count)
        print('  - best solution  : %i' % schedule_builder.BestObjectiveBound())
        print('  - cp len         : %i' % G.cp_len())

        print(schedule_builder.min_schedule())


class ScheduleBuilder(cp_model.CpSolverSolutionCallback):
    def __init__(self, G, M, instances):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.S = schedule.Schedule()
        self.solution_count = 0
        self.G = G
        self.M = M
        self.instances = instances
        self.Ss = []

    def on_solution_callback(self):
        self.solution_count += 1

        S = schedule.Schedule()
        for k, i in self.instances.items():
            if self.Value(i.active):
                interval = po.closedopen(self.Value(i.t_s), self.Value(i.t_f))
                instance = schedule.Instance(i.task, i.pe, i.location, interval)
                scheduled_task = task.ScheduledTask(i.task, instance)
                S.add_task(scheduled_task)
        self.Ss.append(S)

    def min_schedule(self):
        return min(self.Ss, key = lambda s: s.length())
