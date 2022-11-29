from resch import schedule, machine
from resch.heft import original
import functools
import portion as po

class REFT(original.HEFT):
    def rank_task(self, v):
        rank = super().rank_task(v)
        return rank

    def finish_time(self, v, p, loc = machine.Location(0)):
        t_s = self.start_time(v, p, loc = loc)

        return t_s + self.duration(v, p)

    @functools.cache
    def rank_u(self, v):
        w_bar = self.w[v].mean()
        out_costs = [self.cbar(v, n) + self.rank_u(n) - self.pressure(v, n) for n in self.g.iter_out_neighbors(v)]
        return w_bar + max(out_costs, default = 0)

    def allocate(self, v):
        #minimize EFT for all PEs
        f_ts = []
        for p in self.possible_pes(v):
            for loc in p.configuration.locations:
                f_ts.append((self.finish_time(v, p, loc), p, loc))
        eft = min(f_ts, key = lambda t: t[0])

        t_f = eft[0]
        p = eft[1]
        l = eft[2]
        t_s = self.start_time(v, p, l)

        interval = po.closedopen(t_s, t_f)
        instance = schedule.Instance(p, l, interval)
        self.S.add_task(schedule.ScheduledTask.from_node(self.g, v, interval, instance))

    # A number representing the probability from having to add reconfiguration overhead between two tasks
    def pressure(self, v0, v1):
        v0_pes = self.possible_pes(v0)
        v1_pes = self.possible_pes(v1)

        
        v0_instances = []
        v1_instances = []
        for p in v0_pes:
            for l in p.configuration.locations:
                v0_instances.append((p.configuration.index, l.index))
        for p in v1_pes:
            for l in p.configuration.locations:
                v1_instances.append((p.configuration.index, l.index, l.properties.get('c', 0)))
                
        pre = 0
        for a in v0_instances:
            for b in v1_instances:
                pre += pow(0, abs(a[1] - b[1])) * (1 - pow(0, abs(a[0] - b[0]))) * b[2]


        # TODO here!
        return pre / (len(v0_instances) * len(v1_instances))




def build_schedule(g, w, c, m):
    return REFT(g, w, c, m).schedule()
