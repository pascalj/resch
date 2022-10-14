class Task:
    def __init__(self, index, label, cost, dependencies, ttype = None):
        self.index = index
        self.label = label
        self.cost = cost
        self.dependencies = dependencies
        self.type = ttype
        


