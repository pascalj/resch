from resch import machine, task
from resch.heft import original
from queue import PriorityQueue


class CPOP(original.HEFT):
    def rank_task(self, v):
        return self.rank_u(v) + self.rank_d(v)

    def schedule(self):
        cp_set = self.cp_set()

        best_pe = min([(sum(self.w[v, p] for v in cp_set), p) for p in range(self.w.shape[1])], key = lambda t : t[0])[1]

        ready_set = PriorityQueue()
        entry_task = self.entry_tasks()[0]
        ready_set.put((self.rank_task(entry_task), entry_task))

        done_tasks = {}
        for t in self.g.iter_vertices():
            done_tasks[t] = False

        while not ready_set.empty():
            priority, t = ready_set.get()
            p = None
            if t in cp_set:
                t_s = self.start_time(t, best_pe)
                p = best_pe
            else:
                t_f, p = self.eft(t)
            pe = machine.PE(p, machine.Configuration(0, [0]), [])
            self.S.add_task(task.ScheduledTask(task.Task(t, t, self.duration(t, best_pe), []), self.start_time(t, p), pe, 0))
            done_tasks[t] = True
            for n in self.g.iter_out_neighbors(t):
                if all(done_tasks[p] for p in self.g.iter_in_neighbors(n)):
                    ready_set.put((self.rank_task(n), n))

        return self.S

    def cp_len(self):
        return max([self.rank_task(v) for v in self.g.iter_vertices()])
    
    def cp_set(self):
        entry_tasks = self.entry_tasks()
        exit_tasks = self.exit_tasks()

        n_k = entry_tasks[0]
        set_cp = [n_k]

        while n_k not in exit_tasks:
            candidates = [n for n in self.g.iter_out_neighbors(n_k) if self.rank_task(n) == self.cp_len()]
            n_j = candidates[0]
            set_cp.append(n_j)
            n_k = n_j

        return set_cp

    # TODO: reduce to only one task
    def entry_tasks(self):
        return list(filter(lambda v: self.g.vertex(v).in_degree() == 0, self.g.iter_vertices()))

    def exit_tasks(self):
        return list(filter(lambda v: self.g.vertex(v).out_degree() == 0, self.g.iter_vertices()))


def build_schedule(g, w, c):
    return CPOP(g, w, c).schedule()

