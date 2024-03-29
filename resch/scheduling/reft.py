import portion as po
from collections import defaultdict

import resch.scheduling.schedule as schedule
import resch.scheduling.task as task_m

class REFT:
    def __init__(self, M, G, E_cls = schedule.NoEdgeSchedule):
        self.M = M
        self.G = G
        self.S = schedule.Schedule()
        self.E = E_cls(G, M)

    def schedule(self):
        sorted_tasks = self.G.sorted_by_urank()

        for task in sorted_tasks:
            min = po.closedopen(0, po.inf)
            min_p = None
            min_l = None
            for l in self.M.locations():
                overhead = self.M.properties[l].get("r", 0)
                for p in self.M.PEs():
                    # print(task.index, self.M.properties[p]["t"], task.type)
                    if "t" in self.M.properties[p] and self.M.properties[p]["t"] != task.type:
                        continue
                    earliest = po.closedopen(self.data_ready_time(task, p, l), po.inf)
                    interval = self.S.EFT(task, p, l, earliest, overhead)
                    if interval.upper < min.upper: # earliest finish time 8)
                        min = interval
                        min_p = p
                        min_l = l

            assert(min_p)
            assert(min_l)

            # Do the allocation
            dependencies = [int(i) for i in self.G.dependencies(task)]
            edge_intervals = []
            for instance in self.S.instances:
                if instance.task.index in dependencies:
                    edge_intervals.append(self.E.allocate_path(instance, task, min_p, min_l))

            overhead = self.M.properties[min_l].get("r", 0)
            real_DFT = max([i.upper for i in edge_intervals], default = min.lower)
            real_EFT = self.S.EFT(task, min_p, min_l, po.closedopen(real_DFT, po.inf), overhead)

            instance = schedule.Instance(task, min_p, min_l, real_EFT)
            scheduled_task = task_m.ScheduledTask(task, instance)

            # Schedule the task
            self.S.add_task(scheduled_task)

        return (self.S, self.E)

    def data_ready_time(self, task, dst_PE, dst_loc):
        dependencies = [int(i) for i in self.G.dependencies(task)]

        instances = []
        for instance in self.S.instances:
            if instance.task.index in dependencies:
                instances.append(instance)

        return max([self.E.edge_finish_time(i, task, dst_PE, dst_loc) for i in instances], default=0)

