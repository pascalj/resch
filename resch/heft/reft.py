from resch import schedule, machine
from resch.heft import original

class REFT(original.HEFT):
    def rank_task(self, v):
        rank = super().rank_task(v)
        return rank

    def allocate(self, v):
        #minimize EFT for all PEs
        f_ts = []
        for p in self.possible_pes(v):
            for loc in p.configuration.locations:
                f_ts.append((self.finish_time(v, p, loc), p, loc))
        # f_ts = [(self.finish_time(v, p, loc), p, loc) for loc in p.configuration.locations for p in self.possible_pes(v)]
        eft = min(f_ts, key = lambda t: t[0])

        t_f = eft[0]
        p = eft[1]
        l = eft[2]
        t_s = self.start_time(v, p, l)

        instance = schedule.Instance(p, l)
        self.S.add_task(schedule.ScheduledTask.from_node(self.g, v, t_s, instance))



def build_schedule(g, w, c, m):
    return REFT(g, w, c, m).schedule()