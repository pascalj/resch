class Task:
    def __init__(self, index, label, cost, dependencies):
        self.index = index
        self.label = label
        self.cost = cost
        self.dependencies = dependencies

class ScheduledTask(Task):
    def __init__(self, task, t_s, pe, location):
        super().__init__(task.index, task.label, task.cost, task.dependencies)
        self.t_s = t_s
        self.t_f = t_s + self.cost
        self.pe = pe
        self.location = location
