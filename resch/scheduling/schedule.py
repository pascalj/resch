from itertools import chain, pairwise
from functools import reduce
from collections import defaultdict
import portion as po

class Instance:
    def __init__(self, task, pe, location, interval):
        self.config = pe.configuration
        self.pe = pe
        self.location = location
        self.interval = interval
        self.task = task

class Schedule:
    def __init__(self):
        self.tasks = []
        self.instances = []
        self.A_p = defaultdict(lambda: po.IntervalDict()) # [p_id][interval] -> task_id
        self.A_l = defaultdict(lambda: po.IntervalDict()) # [l_id][interval] -> config_id

    def add_task(self, task):
        self.tasks.append(task)
        self.add_instance(task)

    def length(self):
        return max([i.interval.upper for i in self.instances], default=0)

    def task(self, v):
        return next(iter([t for t in self.tasks if t.index == v]), None)

    def EFT(self, task, p, loc, earliest):
        assert(task.index is not None)
        assert(p.index is not None)
        assert(loc.index is not None)

        available = earliest

        # Remove other tasks on the same PE
        available = available - self.A_p[(p.index, loc.index)].domain()

        # Remove other instances on the same location with different configs
        for c_interval, c_id in self.A_l[loc.index].items():
            if c_id != p.configuration.index:
                available = available - c_interval

        for i in available:
            # is the end still in the same slot?
            if po.singleton(i.lower + task.cost[p.index]) <= i:
                return po.closedopen(i.lower, i.lower + task.cost[p.index])

        # Should never arrive here, since we're in [earliest, +inf)
        assert(False)

    def add_instance(self, task):
        instance = task.instance
        self.instances.append(instance)
        p_id = instance.pe.index
        c_id = instance.pe.configuration.index
        l_id = instance.location.index
        t_id = task.index

        # Ensure sure that the PE is not executing any other task
        assert(not self.A_p[(p_id, l_id)].domain().overlaps(instance.interval))
        self.A_p[(p_id, l_id)][instance.interval] = t_id
        # Overlap is allowed if c_id is the same
        self.A_l[l_id][instance.interval] = c_id

    def __str__(self):
        ret = ""
        for loc, interval in self.A_l.items():
            ret += f"Location {loc}\n\t{interval}\n"

        for pe, interval in self.A_p.items():
            ret += f"PE {pe}\n\t{interval}\n"

        return ret
            
