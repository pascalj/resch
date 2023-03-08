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
            earliest = po.closedopen(0, po.inf)

            min = po.closedopen(0, po.inf)
            min_p = None
            min_l = None
            for p in self.M.PEs():
                for l in self.M.locations():
                    interval = self.S.EFT(task, p, l, earliest)
                    if interval.upper < min.upper: # earliest finish time 8)
                        min = interval
                        min_p = p
                        min_l = l

            instance = schedule.Instance(min_p, min_l, interval)
            scheduled_task = task_m.ScheduledTask(task, instance)
            self.S.add_task(scheduled_task)

        return self.S