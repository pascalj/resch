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

    def EFT(self, task, p, loc, earliest, overhead):
        assert(task.index is not None)
        assert(p.index is not None)
        assert(loc.index is not None)

        if task.cost[p.index] == 0:
            return po.singleton(earliest.lower)

        available = earliest

        # Remove other tasks on the same PE
        available = available - self.A_p[(p.index, loc.index)].domain()

        # Remove other instances on the same location with different configs
        for c_interval, c_id in self.A_l[loc.index].items():
            if c_id != p.configuration.index:
                available_pre = available
                int_w_reconf = c_interval.apply(
                        lambda x: x.replace(
                            lower = lambda v: v - overhead,
                            upper = lambda v: v + overhead))
                available = available - int_w_reconf

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

        if instance.interval.lower == instance.interval.upper:
            return

        # Ensure sure that the PE is not executing any other task
        assert not self.A_p[(p_id, l_id)].domain().overlaps(instance.interval),\
             f"{self.A_p[(p_id, l_id)]} and {instance.interval} overlap"

        self.A_p[(p_id, l_id)][instance.interval] = t_id
        # Overlap is allowed if c_id is the same
        self.A_l[l_id][instance.interval] = c_id

    def instances_for_tasks(self, tasks):
        int_tasks = [int(t) for t in tasks]
        return [i for i in self.instances if i.task.index in int_tasks]

    def instance(self, task):
        instance = [i for i in self.instances if i.task.index == task.index]
        assert len(instance) == 1
        return instance[0]

    def validate(self, G, M):
        for task in G.tasks():
            t_instance = self.instance(task)
            for dep in G.task_dependencies(task):
                dep_instance = self.instance(dep)
                if dep_instance.interval.lower != dep_instance.interval.upper:
                    assert t_instance.interval > self.instance(dep).interval, f"{t_instance.interval} should come after {self.instance(dep).interval}"

        for loc in M.locations():
            overhead = M.properties[loc].get("r", 0)
            for lhs, rhs in pairwise(self.A_l[loc.index]):
                lhs_with_overhead = lhs.apply(lambda x: x.replace(upper = lambda v: v + overhead, lower=lambda v: v - overhead) if x.lower != x.upper else x)
                assert (lhs_with_overhead & rhs).empty,\
                    f"{lhs} to {rhs} requires {overhead} overhead ({lhs_with_overhead & rhs})"


    def to_csv(self, file_handle):
        rows = ["config,pe,location,t_s,t_f,task\n"]
        for i in self.instances:
            rows.append(f"{i.config.index},{i.pe.index},{i.location.index},{i.interval.lower},{i.interval.upper},{i.task.index}\n")

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

    def add_interval(self, *arg):
        pass

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

        if cost == 0:
            return t_f

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

    def allocate_path(self, src_instance, dst_task, dst_PE, dst_loc):
        path = self.topo.pe_path(src_instance.placed_pe(), (dst_PE.index, dst_loc.index))
        if len(path) == 0:
            return po.singleton(src_instance.interval.upper)

        cost = self.G.edge_cost(src_instance.task, dst_task)
        lower_bound = src_instance.interval.upper

        if cost == 0:
            return po.singleton(src_instance.interval.upper)

        interval = self.available_path_interval(path, cost, lower_bound)

        for link in path:
            self.allocate_edge(link, src_instance, dst_task, cost, interval)

        return interval

    def allocate_edge(self, link, src_instance, dst_task, cost, interval):
        if cost == 0:
            return
        link_cost = cost / self.topo.relative_capacity(link)
        link_interval = po.closedopen(interval.upper - link_cost, interval.upper)
        assert(not self.A_l[link].domain().overlaps(interval))
        self.A_l[link][interval] = (src_instance.task.index, dst_task.index)

    def add_interval(self, link, interval, src_task_index, dst_task_index):
        self.A_l[link][interval] = (src_task_index, dst_task_index)


    def to_csv(self, file_handle):
        rows = ["t_s,t_f,link,from,to\n"]
        links = sorted(self.A_l.keys())
        for link in links:
            for interval, edge in self.A_l[link].items():
                link_id = f"{link.source()}-{link.target()}"
                rows.append(f"{interval.lower},{interval.upper},{link_id},{edge[0]},{edge[1]}\n")
        file_handle.writelines(rows)


    def __str__(self):
        ret = ""
        for link, interval in self.A_l.items():
            ret += f"Link {link}\n\t{interval}\n"

        return ret
