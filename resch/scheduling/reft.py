import portion as po
from collections import defaultdict

import resch.scheduling.schedule as schedule
import resch.scheduling.task as task_m

class REFT:
    def __init__(self, M, G):
        self.M = M
        self.G = G
        self.S = schedule.Schedule()

    def schedule(self):
        sorted_tasks = self.G.sorted_by_urank()

        for task in sorted_tasks:
            # TODO: min start time
            earliest = po.closedopen(self.data_ready_time(task.index), po.inf)

            min = po.closedopen(0, po.inf)
            min_p = None
            min_l = None
            for l in self.M.locations():
                for p in self.M.PEs():
                    interval = self.S.EFT(task, p, l, earliest)
                    if interval.upper < min.upper: # earliest finish time 8)
                        min = interval
                        min_p = p
                        min_l = l

            instance = schedule.Instance(task, min_p, min_l, interval)
            scheduled_task = task_m.ScheduledTask(task, instance)
            self.S.add_task(scheduled_task)

        return self.S

    def data_ready_time(self, task_id):
        dependencies = [int(i) for i in self.G.dependencies(task_id)]
        return max(
                [instance.interval.upper for instance in self.S.instances
                    if instance.task.index in dependencies],
                default=0)
