# List scheduling implementation

from resch import task, graph, schedule
from collections import defaultdict

class ListScheduler:
    def __init__(self, m):
        self.m = m
        self.S = schedule.Schedule()
        self.asap = defaultdict(lambda: 0)

    def build(self, g):
        # Topologically sorted tasks
        sorted_tasks = g.sorted_tasks()

        # Get p and t_s for each task
        for v in sorted_tasks:
            pe       = self.select_pe_constrained(v)
            location = self.select_location(v, pe)
            t_s      = self.schedule_constrained(v, pe, location)

            self.S.add_task(ScheduledTask(v, t_s, pe, location))
        return self.S

    def select_pe_constrained(self, v):
        for pe in self.m.PEs:
            if pe.properties['p_ft'] == v.type:
                # TODO: strategy
                return pe

    def select_location(self, v, pe):
        for location in pe.configuration.locations:
            return location

    def schedule_constrained(self, v, pe, location):
        t_s = self.asap[pe];
        self.asap[pe] = t_s + v.cost
        return t_s

# For a constistent interface across approaches
def build_schedule(m, g):
    scheduler = Scheduler(m)
    return scheduler.build(g)
