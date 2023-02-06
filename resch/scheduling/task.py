class Task:
    def __init__(self, index, label, cost, dependencies, ttype = None):
        self.index = index
        self.label = label
        self.cost = cost
        self.dependencies = dependencies
        self.type = ttype

class ScheduledTask(Task):
    def __init__(self, task, interval, instance):
        super().__init__(task.index, task.label, task.cost, task.dependencies, ttype = task.type)
        self.t_s = interval.lower
        self.t_f = interval.lower + self.cost
        self.pe = instance.pe
        self.location = instance.location
        self.interval = interval
        self.instance = instance

    @classmethod
    def from_node(cls, g, v, t_s, instance):
        t = task.Task(v, g.vp.label[v], g.vp.cost[v][instance.pe.index], g.get_in_neighbors(v), ttype = g.vp.type[v])
        return cls(t, t_s, instance)
