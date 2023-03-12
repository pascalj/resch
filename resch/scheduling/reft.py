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
            # TODO: this needs to happen per dependency (see scheduly.py:83)
            # and should move the t_s for task back for each of the
            # dependencies. This means for EdgeSchedule there must be something
            # equivalent to equivalent to ll schedule.py:84

            min = po.closedopen(0, po.inf)
            min_p = None
            min_l = None
            for l in self.M.locations():
                for p in self.M.PEs():
                    earliest = po.closedopen(self.data_ready_time(task, p, l), po.inf)
                    interval = self.S.EFT(task, p, l, earliest)
                    if interval.upper < min.upper: # earliest finish time 8)
                        min = interval
                        min_p = p
                        min_l = l

            # Do the allocation
            dependencies = [int(i) for i in self.G.dependencies(task)]
            edge_intervals = []
            for instance in self.S.instances:
                if instance.task.index in dependencies:
                    edge_intervals.append(self.E.allocate_path(instance, task, min_p, min_l))

            real_DFT = max([i.upper for i in edge_intervals], default = min.lower)
            real_EFT = self.S.EFT(task, min_p, min_l, po.closedopen(real_DFT, po.inf))

            instance = schedule.Instance(task, min_p, min_l, real_EFT)
            scheduled_task = task_m.ScheduledTask(task, instance)

            # Schedule the task
            self.S.add_task(scheduled_task)
            # Schedule edges in the edge schedule for all dependencies
            # for instance in self.S.instances_for_tasks(self.G.dependencies(task)):
            #     self.E.add_task(instance, scheduled_task)

        return self.S

    def data_ready_time(self, task, dst_PE, dst_loc):
        dependencies = [int(i) for i in self.G.dependencies(task)]

        instances = []
        for instance in self.S.instances:
            if instance.task.index in dependencies:
                instances.append(instance)

        return max([self.E.edge_finish_time(i, task, dst_PE, dst_loc) for i in instances], default=0)

