import collections
import random
from ortools.sat.python import cp_model

import svgwrite
from resch import schedule
from resch import task as t

PEs_count = 3


# TODO: remove this
tasks_to_pes = [[0], [0], [1], [1], [2], [2]]

P = range(PEs_count)
P_or = 10

# Takes a graph and machine models and gets the optimal schedule
def build_schedule(m, g):
    model = cp_model.CpModel()

    horizon = sum(task.cost for task in g.tasks) + len(g.tasks) * P_or

    interval_type = collections.namedtuple('interval_type', 'task pe start end duration interval mapped location')
    intervals = {}

    all_tasks = {}
    pes_to_tasks = {}

    for task in g.tasks:
        task_id = task.index
        duration = task.cost
        for pe in m.PEs:
            suffix = '[%i,%i]' % (task_id, pe.index)
            start_var = model.NewIntVar(0, horizon, 'start' + suffix)
            end_var = model.NewIntVar(0, horizon, 'end' + suffix)
            duration_var = model.NewIntVar(duration, duration, 'duration' + suffix)
            mapped_var = model.NewBoolVar('pes_to_tasks[%i][%i]' % (pe.index, task_id))
            interval_var = model.NewOptionalIntervalVar(start_var, duration_var, end_var, mapped_var,  'interval' + suffix)
            location_var = model.NewIntVarFromDomain(cp_model.Domain.FromValues([l.index for l in pe.configuration.locations]), 'location[%i][%i]' % (pe.configuration.index, task_id))

            # Enforce P_ft
            if pe.index not in tasks_to_pes[task_id]:
                model.AddAbsEquality(0, mapped_var)
            intervals[(task_id,pe.index)] = interval_type(start=start_var, end=end_var, duration=duration_var,mapped=mapped_var, pe=pe, task=task_id, interval=interval_var, location=location_var)

    for pe in m.PEs:
        pe_intervals = [intervals[(task.index, pe.index)] for task in g.tasks]
        model.AddNoOverlap(interval.interval for interval in pe_intervals)

    for task in g.tasks:
        task_id = task.index
        task_intervals = [intervals[(task_id, pe.index)] for pe in m.PEs]
        # Have exactly one mapped interval/task
        model.Add(sum(interval.mapped for interval in task_intervals) == 1)

    for task in g.tasks:
        task_id = task.index
        task_dependencies = task.dependencies
        for task_pe in m.PEs:
            for dependency in task_dependencies:
                for pe in m.PEs:
                    model.Add(intervals[(task_id,task_pe.index)].start >= intervals[(dependency, pe.index)].end)

    for a in intervals.values():
        for b in intervals.values():
            if a != b and a.pe.configuration != b.pe.configuration:
                same_location = model.NewBoolVar(f'same_location{a.task}_{a.pe.index}_{b.task}_{b.pe.index}')
                model.Add(a.location == b.location).OnlyEnforceIf(same_location)
                model.Add(a.location != b.location).OnlyEnforceIf(same_location.Not())
                either_or = model.NewBoolVar(f'inter_{a.task}_{b.task}')
                model.Add(a.start >= b.end + P_or).OnlyEnforceIf(either_or).OnlyEnforceIf(same_location)
                model.Add(b.start >= a.end + P_or).OnlyEnforceIf(either_or.Not()).OnlyEnforceIf(same_location)

    obj_var = model.NewIntVar(0, horizon, 'makespan')
    model.AddMaxEquality(obj_var, [interval.end for _, interval in enumerate(intervals.values())])
    model.Minimize(obj_var)


    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:

        S = schedule.Schedule()
        for task in g.tasks:
            for pe in m.PEs:
                interval = intervals[(task.index, pe.index)]
                if solver.Value(interval.mapped):
                    t_s = solver.Value(interval.start)
                    location = solver.Value(interval.location)
                    task = t.ScheduledTask(g.tasks[task.index], t_s, pe, location)
                    S.add_task(task)

        return S
    else:
        return None
                



