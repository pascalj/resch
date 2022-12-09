import schedule, task, machine
import functools
import portion as P

# w[task, p]
# c[task, task]
class HEFT:
    def __init__(self, g, w, c, m):
        self.g = g
        self.w = w
        self.c = c
        self.S = schedule.Schedule()
        self.m = m

    def cbar(self, f, t):
        # get the mean of all cost from task f to t
        return self.c[f, t].mean()

    def rank_task(self, v):
        return self.rank_u(v)

    @functools.cache
    def rank_u(self, v):
        w_bar = self.w[v].mean()
        out_costs = [self.cbar(v, n) + self.rank_u(n) for n in self.g.iter_out_neighbors(v)]
        return w_bar + max(out_costs, default = 0)

    @functools.cache
    def rank_d(self, v):
        w_bar = lambda v : self.w[v].mean()
        rank_cost = [self.rank_d(n) + w_bar(n) + self.cbar(v, n) for n in self.g.iter_in_neighbors(v)]
        return max(rank_cost, default = 0)


    def start_time(self, v, p, loc = machine.Location(0)):
        return self.S.earliest_gap(p, loc, self.edge_finish_time(v), self.duration(v, p))

    def eft(self, v):
        return min([(self.finish_time(v, p), p) for p in self.possible_pes(v)], key = lambda t: t[0])

    def edge_finish_time(self, v):
        # TODO: location
        return max([self.S.task(n).t_f + self.c[n, v, 0, 0] for n in self.g.iter_in_neighbors(v)], default = 0)

    def finish_time(self, v, p, loc = machine.Location(0)):
        t_s = self.start_time(v, p, loc = loc)

        return t_s + self.duration(v, p)

    def duration(self, v, p):
        return self.w[v, p.index]

    def allocate(self, v):
        #minimize EFT for all PEs
        f_ts = [(self.finish_time(v, p), p) for p in self.possible_pes(v)]
        eft = min(f_ts, key = lambda t: t[0])

        t_f = eft[0]
        p = eft[1]
        t_s = self.start_time(v, p)

        instance = schedule.Instance(p, machine.Location(0), P.closedopen(t_s, t_f))
        self.S.add_task(schedule.ScheduledTask.from_node(self.g, v, t_s, instance))

    def schedule(self):
        ordered_tasks = sorted(self.g.get_vertices(), key = lambda v: self.rank_task(v))

        for t in reversed(ordered_tasks):
            self.allocate(t)

        return self.S

    def possible_pes(self, v):
        ttype = self.g.vp.type[v]

        if ttype is None:
            return self.m.PEs

        possible = filter(lambda p: p.type == None or ttype == p.type, self.m.PEs)
        return possible

def build_schedule(g, w, c, m):
    return HEFT(g, w, c, m).schedule()
