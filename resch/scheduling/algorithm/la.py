from resch import machine, task
from resch.heft import original
from copy import deepcopy

# 10.1109/PDP.2010.56

class HEFTla(original.HEFT):
    def allocate(self, v):
        #minimize EFT for all PEs
        num_pes = self.w.shape[1]

        eft_min = min([(self.simulate_allocate(v, p), p) for p in range(num_pes)], key = lambda t: t[0])
        p = eft_min[1]

        t_s = self.start_time(v, p)
        t_f = self.finish_time(v, p)

        pe = machine.PE(p, machine.Configuration(0, [0]), [])
        self.S.add_task(task.ScheduledTask(task.Task(v, v, self.duration(v, p), []), t_s, pe, 0))

    def simulate_allocate(self, v, p):
        original_S = deepcopy(self.S)

        heft = original.HEFT(self.g, self.w, self.c, S=original_S)

        pe = machine.PE(p, machine.Configuration(0, [0]), [])
        heft.S.add_task(task.ScheduledTask(task.Task(v, v, heft.duration(v, p), []), heft.start_time(v, p), pe, 0))

        for n in heft.g.iter_out_neighbors(v):
            heft.allocate(n)

        return max([heft.S.task(n).t_f for n in heft.g.iter_out_neighbors(v)], default = 0)


def build_schedule(g, w, c):
    return HEFTla(g, w, c).schedule()
