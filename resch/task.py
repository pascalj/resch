class Task:
    def __init__(self, index, label, cost, dependencies, ttype = None):
        self.index = index
        self.label = label
        self.cost = cost
        self.dependencies = dependencies
        self.type = ttype
        


class ScheduledTask(Task):
    @classmethod
    def from_node(cls, g, v, t_s, pe, location):
        task = Task(v, g.vp.label[v], g.vp.cost[v][pe.index], g.get_in_neighbors(v), ttype = g.vp.type[v])
        return cls(task, t_s, pe, location)

    def __init__(self, task, t_s, pe, location):
        super().__init__(task.index, task.label, task.cost, task.dependencies, ttype = task.type)
        self.t_s = t_s
        self.t_f = t_s + self.cost
        self.pe = pe
        self.location = location
