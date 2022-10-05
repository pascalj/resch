from resch import schedule, task, machine
import functools

# w[task, p]
# c[task, task]
class HEFT:

    def __init__(self, g, w, c, S = None):
        self.g = g
        self.w = w
        self.c = c
        if S:
            self.S = S
        else:
            self.S = schedule.Schedule()

    def cbar(self, f, t):
        # get the mean of all cost from task f to t
        return self.c[f, t].mean()


    @functools.cache
    def rank_task(self, v):
        w_bar = self.w[v].mean()
        if self.g.vertex(v).out_degree() > 0:
            return w_bar + max(self.cbar(v, n) + self.rank_task(n) for n in self.g.iter_out_neighbors(v))
        else:
            return w_bar

    def start_time(self, v, p):
        duration = self.w[v, p]

        ready_at = 0
        if self.g.vertex(v).in_degree() > 0:
            ready_at = max([(self.S.task(n).t_f + self.c[n, v, self.S.task(n).pe.index, p]) if self.S.task(n) else 0 for n in self.g.iter_in_neighbors(v)])

        return self.S.earliest_gap(p, ready_at, duration)

    def finish_time(self, v, p):
        t_s = self.start_time(v, p)
        duration = self.w[v, p]

        return t_s + duration;

    def duration(self, v, p):
        return self.w[v, p]

    def allocate(self, v):
        #minimize EFT for all PEs
        num_pes = self.w.shape[1]
        eft = min([(self.start_time(v, p), self.finish_time(v, p), p) for p in range(num_pes)], key = lambda t: t[1])
        t_s = eft[0]
        t_f = eft[1]
        p = eft[2]

        pe = machine.PE(p, machine.Configuration(0, [0]), [])
        self.S.add_task(task.ScheduledTask(task.Task(v, v, self.duration(v, p), []), t_s, pe, 0))

    def schedule(self):
        ordered_tasks = sorted(self.g.get_vertices(), key = lambda v: self.rank_task(v))

        for t in reversed(ordered_tasks):
            self.allocate(t)

        return self.S
    

def build_schedule(g, w, c):
    return HEFT(g, w, c).schedule()
