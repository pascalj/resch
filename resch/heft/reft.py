from resch import schedule
from resch.heft import original

class REFT(original.HEFT):
    def rank_task(self, v):
        rank = super().rank_task(v)
        return rank



def build_schedule(g, w, c, m):
    return REFT(g, w, c, m).schedule()
