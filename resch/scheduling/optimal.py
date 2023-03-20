import collections
from ortools.sat.python import cp_model

import resch.scheduling.schedule as schedule
import resch.scheduling.task as task
import portion as po


# Takes a graph and machine models and gets the optimal schedule
class OptimalScheduler:
    def __init__(self, M, G, E_cls = schedule.NoEdgeSchedule):
        self.M = M
        self.G = G
        self.E_cls = E_cls

    def schedule(self, debug = False):
        self.model = cp_model.CpModel()
        M = self.M
        G = self.G
        model = self.model

        InstanceVar = collections.namedtuple("Instance", "t_s cost t_f active interval pe location task")
                                                            # ^^^^ only for NewOptionalIntervalVar
        LinkInstanceVar = collections.namedtuple("LinkInstance", "t_s cost t_f interval active")

        horizon = 5000
        instances = {}
        config_active = {}
        edge_instances = {}

        tasks = [G.task(v) for v in G.sorted_topologically()]
        for task in tasks:
            for pe in M.PEs():
                for l in M.locations():
                    suffix = f"_{task.index}_{pe.index}_{l.index}"
                    active = model.NewBoolVar(f"active{suffix}")
                    t_s = model.NewIntVar(0, horizon, f"t_s{suffix}")
                    cost = G.task_cost(task, pe)
                    cost = model.NewIntVar(cost, cost, f"cost{suffix}")
                    t_f = model.NewIntVar(0, horizon, f"t_f{suffix}")
                    interval = model.NewOptionalIntervalVar(t_s, cost, t_f, active, f"active{suffix}")
                    instances[(pe.index, l.index, task.index)] = InstanceVar(active=active, t_s=t_s, cost=cost, t_f=t_f, interval=interval, pe=pe, location=l, task=task)

        # Execute each task on exactly one placed PE
        for task in tasks:
            model.AddExactlyOne(instances[(pe.index, l.index, task.index)].active for pe in M.PEs() for l in M.locations())

        for task in tasks:
            for dependency in G.task_dependencies(task):
                for src_pe in M.PEs():
                    for src_l in M.locations():
                        for dst_pe in M.PEs():
                            for dst_l in M.locations():
                                model.Add(instances[(src_pe.index, src_l.index, dependency.index)].t_f < instances[(dst_pe.index, dst_l.index, task.index)].t_s)
                                if self.E_cls == schedule.EdgeSchedule:
                                    path = self.M.topology.pe_path((src_pe.index, src_l.index), (dst_pe.index, dst_l.index))
                                    src_active = instances[(src_pe.index, src_l.index, dependency.index)].active
                                    dst_active = instances[(dst_pe.index, dst_l.index, task.index)].active
                                    edge_active = model.NewBoolVar("active")
                                    model.Add(edge_active == True).OnlyEnforceIf(src_active).OnlyEnforceIf(dst_active)
                                    model.Add(edge_active == False).OnlyEnforceIf(src_active.Not())
                                    model.Add(edge_active == False).OnlyEnforceIf(dst_active.Not())
                                    edge_cost = G.edge_cost(dependency, task) 
                                    t_f = model.NewIntVar(0, horizon, f"t_f{suffix}")
                                    for link in path:
                                        link_id = link
                                        suffix = f"_{(src_pe.index, src_l.index, dst_pe.index, dst_l.index, dependency.index, task.index, link_id)}"
                                        t_s = model.NewIntVar(0, horizon, f"t_s{suffix}")
                                        cost_val = int(edge_cost / self.M.topology.relative_capacity(link))
                                        cost = model.NewIntVar(cost_val, cost_val, f"cost{suffix}")
                                        model.Add(t_s > instances[(src_pe.index, src_l.index, dependency.index)].t_f).OnlyEnforceIf(edge_active)
                                        model.Add(t_f > instances[(src_pe.index, src_l.index, dependency.index)].t_f).OnlyEnforceIf(edge_active)
                                        model.Add(t_s < instances[(dst_pe.index, dst_l.index, task.index)].t_s).OnlyEnforceIf(edge_active)
                                        model.Add(t_f < instances[(dst_pe.index, dst_l.index, task.index)].t_s).OnlyEnforceIf(edge_active)
                                        interval = model.NewOptionalIntervalVar(t_s, cost, t_f, edge_active, f"interval{suffix}")
                                        instance = LinkInstanceVar(t_s=t_s, cost=cost, t_f=t_f, interval=interval, active=edge_active)
                                        assert((src_pe.index, src_l.index, dst_pe.index, dst_l.index, dependency.index, task.index, link_id) not in edge_instances)
                                        edge_instances[(src_pe.index, src_l.index, dst_pe.index, dst_l.index, dependency.index, task.index, link_id)] = instance
                                        

        # No overlap
        for pe in M.PEs():
            for l in M.locations():
                model.AddNoOverlap(instances[(pe.index, l.index, task.index)].interval for task in tasks)

        for link in self.M.topology.g.edges():
            link_instances = [edge_instances[k] for k in edge_instances.keys() if k[6] == link]
            model.AddNoOverlap(i.interval for i in link_instances)


        obj_var = model.NewIntVar(0, horizon, 'makespan')
        model.AddMaxEquality(obj_var, [i.t_f for k, i in instances.items()])
        model.Minimize(obj_var)

        solver = cp_model.CpSolver()
        schedule_builder = ScheduleBuilder(G, M, instances, edge_instances, self.E_cls)

        solver.Solve(model, schedule_builder)
        if debug:
            print('\nStatistics')
            print('  - conflicts      : %i' % solver.NumConflicts())
            print('  - branches       : %i' % solver.NumBranches())
            print('  - wall time      : %f s' % solver.WallTime())
            print('  - solutions found: %i' % schedule_builder.solution_count)
            print('  - best solution  : %i' % schedule_builder.BestObjectiveBound())
            print('  - cp len         : %i' % G.cp_len())

            print(schedule_builder.min_schedule())

        return schedule_builder.min_schedule()


class ScheduleBuilder(cp_model.CpSolverSolutionCallback):
    def __init__(self, G, M, instances, edge_instances, E_cls):
        cp_model.CpSolverSolutionCallback.__init__(self)
        self.S = schedule.Schedule()
        self.solution_count = 0
        self.G = G
        self.M = M
        self.instances = instances
        self.edge_instances = edge_instances
        self.Ss = []
        self.Es = []
        self.E_cls = E_cls

    def on_solution_callback(self):
        self.solution_count += 1

        S = schedule.Schedule()
        E = self.E_cls(self.G, self.M)
        for k, i in self.instances.items():
            if self.Value(i.active):
                interval = po.closedopen(self.Value(i.t_s), self.Value(i.t_f))
                instance = schedule.Instance(i.task, i.pe, i.location, interval)
                scheduled_task = task.ScheduledTask(i.task, instance)
                S.add_task(scheduled_task)
        for k, i in self.edge_instances.items():
            if self.Value(i.active):
                (src_pe, src_l, dst_pe, dst_l, src_task_index, dst_task_index, link) = k
                assert(self.Value(self.instances[(src_pe, src_l, src_task_index)].t_f) < self.Value(i.t_s))
                assert(self.Value(self.instances[(src_pe, src_l, src_task_index)].t_f) < self.Value(i.t_f))
                interval = po.closedopen(self.Value(i.t_s), self.Value(i.t_f))
                E.add_interval(link, interval, src_task_index, dst_task_index)
        self.Ss.append(S)
        self.Es.append(E)

    def min_schedule(self):
        minpos = self.Ss.index(min(self.Ss, key = lambda s: s.length()))
        return (self.Ss[minpos], self.Es[minpos])
