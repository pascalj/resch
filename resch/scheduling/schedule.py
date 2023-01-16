from itertools import chain, pairwise
from functools import reduce
import task
import portion as po

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

    def __init__(self, task, interval, instance):
        super().__init__(task.index, task.label, task.cost, task.dependencies, ttype = task.type)
        self.t_s = interval.lower
        self.t_f = interval.lower + self.cost
        self.pe = instance.pe
        self.location = instance.location
        self.interval = interval
        self.instance = instance

class Schedule:
    def __init__(self):
        self.tasks = []
        self.instances = []

    def add_task(self, task):
        self.tasks.append(task)
        self.add_instance(task.instance)

    def length(self):
        return max(task.t_s + task.cost for task in self.tasks)

    def task(self, v):
        return next(iter([t for t in self.tasks if t.index == v]), None)

    def earliest_gap(self, p, loc, earliest, duration):
        assert(p.index is not None)

        l_c = loc.properties.get('c', 0)

        p_tasks = [t for t in self.tasks if t.pe == p and loc == t.location]

        conflict_instances = [i for i in self.instances if i.location == loc and i.config != p.configuration]

        # insert conflict here
        p_c = p.properties.get('c', [])
        p_s = p.properties.get('s', 0)
        conflict_tasks = [t for t in self.tasks if t.pe in p_c]

        available = po.closedopen(earliest, po.inf)

        for t in p_tasks:
            available = available - t.interval

        for i in conflict_instances:
            reconf_interval = i.interval.replace(upper=lambda x: x + l_c)
            available = available - reconf_interval

        for i in conflict_tasks:
            available = available - i.interval
  
        for i in available:
            # is the end still in the same slot?
            if po.singleton(i.lower + p_s + duration) <= i:
                return i.lower + p_s

        # Should never arrive here, since we're in [earliest, +inf)
        assert(fail)

    def add_instance(self, instance):
        self.instances.append(instance)


    def makespan(self):
        return max(t.t_f for t in self.tasks)

