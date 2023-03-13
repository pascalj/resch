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

    def placed_pe(self):
        return (self.pe.index, self.location.index)

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
        if self.A_p[(p_id, l_id)].domain().overlaps(instance.interval):
            assert(False)
        self.A_p[(p_id, l_id)][instance.interval] = t_id
        # Overlap is allowed if c_id is the same
        self.A_l[l_id][instance.interval] = c_id

    def instances_for_tasks(self, tasks):
        int_tasks = [int(t) for t in tasks]
        return [i for i in self.instances if i.task.index in int_tasks]

    def to_csv(self, file_handle):
        rows = [f"{i.config.index},{i.pe.index},{i.location.index},{i.interval.lower},{i.interval.upper},{i.task.index}\n"
            for i in self.instances]
            
        file_handle.writelines(rows)

    def __str__(self):
        ret = ""
        for loc, interval in self.A_l.items():
            ret += f"Location {loc}\n\t{interval}\n"

        for pe, interval in self.A_p.items():
            ret += f"PE {pe}\n\t{interval}\n"

        return ret
            
class NoEdgeSchedule:
    def __init__(self, G, M):
        self.G = G
        self.topo = M.topology

    def edge_finish_time(self, src_instance, dst, dst_PE, dst_loc):
        is_local = (dst_PE == src_instance.pe and dst_loc == src_instance.location)
        t_f = src_instance.interval.upper
        if is_local:
            return t_f

        edge_cost = self.G.edge_cost(src_instance.task, dst)

        return t_f + edge_cost

    def add_task(self, task, _):
        pass

    def allocate_path(self, instance, *arg):
        return po.singleton(instance.interval.upper)

    def __str__(self):
        return "No edge schedule"

class EdgeSchedule:
    def __init__(self, G, M):
        self.A_l = defaultdict(lambda: po.IntervalDict()) # link -> intervals
        self.G = G
        self.topo = M.topology

    def edge_finish_time(self, src_instance, dst_task, dst_PE, dst_loc):
        is_local = (dst_PE == src_instance.pe and dst_loc == src_instance.location)
        t_f = src_instance.interval.upper
        if is_local:
            return t_f

        cost = self.G.edge_cost(src_instance.task, dst_task)
        path = self.topo.pe_path(src_instance.placed_pe(), (dst_PE.index, dst_loc.index))

        available_interval = self.available_path_interval(path, cost, t_f)

        return available_interval.upper


    def available_path_interval(self, path, cost, lower_bound):
        available = po.closedopen(lower_bound, po.inf)
        min_capacity = min(self.topo.relative_capacity(link) for link in path)
        for link in path:
            available = available - self.A_l[link].domain()

        max_link_cost = cost / min_capacity

        upper = lower_bound
        for interval in available:
            if po.singleton(interval.lower + max_link_cost) <= interval:
                 upper = interval.lower + max_link_cost
                 return po.closedopen(interval.lower, interval.lower + max_link_cost)

        assert(False)

    # def add_task(self, src_instance, scheduled_task):
    #     if src_instance.pe == scheduled_task.instance.pe:
    #         return

    #     self.allocate_path(src_instance, scheduled_task, scheduled_task.instance.interval.lower)

    def allocate_path(self, src_instance, dst_task, dst_PE, dst_loc):
        path = self.topo.pe_path(src_instance.placed_pe(), (dst_PE.index, dst_loc.index))
        if len(path) == 0:
            return po.singleton(src_instance.interval.upper)

        cost = self.G.edge_cost(src_instance.task, dst_task)
        lower_bound = src_instance.interval.upper

        interval = self.available_path_interval(path, cost, lower_bound)

        for link in path:
            self.allocate_edge(link, src_instance, dst_task, cost, interval)

        return interval

    def allocate_edge(self, link, src_instance, dst_task, cost, interval):
        link_cost = cost / self.topo.relative_capacity(link)
        link_interval = po.closedopen(interval.upper - link_cost, interval.upper)
        assert(not self.A_l[link].domain().overlaps(interval))
        self.A_l[link][interval] = (src_instance.task.index, dst_task.index)

    def __str__(self):
        ret = ""
        for link, interval in self.A_l.items():
            ret += f"Link {link}\n\t{interval}\n"

        return ret
