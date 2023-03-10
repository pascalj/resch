import portion as po
from collections import defaultdict

import resch.scheduling.schedule as schedule
import resch.scheduling.task as task_m

class REFT:
    def __init__(self, M, G, E = lambda G, M: schedule.NoEdgeSchedule(G, M.topology)):
        self.M = M
        self.G = G
        self.S = schedule.Schedule()
        self.E = E(G, M)

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
                    earliest = po.closedopen(self.data_ready_time(task, p.index), po.inf)
                    interval = self.S.EFT(task, p, l, earliest)
                    if interval.upper < min.upper: # earliest finish time 8)
                        min = interval
                        min_p = p
                        min_l = l

            instance = schedule.Instance(task, min_p, min_l, interval)
            scheduled_task = task_m.ScheduledTask(task, instance)
            self.S.add_task(scheduled_task)

        return self.S

    def data_ready_time(self, task, PE_index):
        dependencies = [int(i) for i in self.G.dependencies(task.index)]

        instances = []
        for instance in self.S.instances:
            if instance.task.index in dependencies:
                is_local = PE_index == instance.pe.index
                self.E.edge_finish_time(instance, task, is_local)
                instances.append(instance)
        
        return max([i.interval.upper for i in instances], default=0)
