from itertools import chain
from resch import task
import portion as P

class Instance:
    def __init__(self, pe, location, interval):
        self.config = pe.configuration
        self.pe = pe
        self.location = location
        self.interval = interval

class ScheduledTask(task.Task):
    @classmethod
    def from_node(cls, g, v, t_s, instance):
        t = task.Task(v, g.vp.label[v], g.vp.cost[v][instance.pe.index], g.get_in_neighbors(v), ttype = g.vp.type[v])
        return cls(t, t_s, instance)

    def __init__(self, task, t_s, instance):
        super().__init__(task.index, task.label, task.cost, task.dependencies, ttype = task.type)
        self.t_s = t_s
        self.t_f = t_s + self.cost
        self.pe = instance.pe
        self.location = instance.location
        self.instance = instance

class Schedule:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)
        self.add_instance(task.instance)

    def length(self):
        return max(task.t_s + task.cost for task in self.tasks)

    def task(self, v):
        return next(iter([t for t in self.tasks if t.index == v]), None)

    def earliest_gap(self, p, loc, earliest, duration):
        assert(p.index is not None)
        p_tasks = list(filter(lambda t: (t.pe.index == p.index) and (loc.index == t.location.index), self.tasks))
        if not p_tasks:
            return earliest

        # ordered_tasks = sorted([task for task in S.tasks if task.location == l], key = lambda t: t.t_s)
        
        p_times = [(t.t_s, t.t_f) for t in p_tasks]
        win = chain((0,0), p_times[:-1])
        for t1, t2 in zip (win, p_times):
            earliest_start = max(earliest, t2[1])
            if t2[0] - earliest_start > duration:
                return earliest_start

        return max(p_times[-1][1], earliest)

    def add_instance(instance):
        loc = instance.location
        loc_instances = [i for i in self.instances if i.location == loc]


        # TODO: here

        for l_instance in loc_instances:
            if l_instance.interval.overlaps(instance.interval):
                assert(l_instance.config == instance.config)
                new_interval = l_instance.interval.union(instance.interval)
                l_instance.interval = new_interval


    def makespan(self):
        return max(t.t_f for t in self.tasks)

