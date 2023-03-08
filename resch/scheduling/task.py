class Task:
    def __init__(self, index, label, cost, ttype = None):
        self.index = index
        self.label = label
        self.cost = cost
        self.type = ttype

class ScheduledTask(Task):
    def __init__(self, task, instance):
        super().__init__(task.index, task.label, task.cost, ttype = task.type)
        self.t_s = instance.interval.lower
        self.t_f = instance.interval.upper
        self.pe = instance.pe
        self.location = instance.location
        self.instance = instance

