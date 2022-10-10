import svgwrite
from itertools import chain
from svgwrite import cm,mm
import matplotlib as mpl
from os.path import dirname
from os import makedirs

class Schedule:
    def __init__(self):
        self.tasks = []

    def add_task(self, task):
        self.tasks.append(task)

    def length(self):
        return max(task.t_s + task.cost for task in self.tasks)

    def task(self, v):
        return next(iter([t for t in self.tasks if t.index == v]), None)

    def earliest_gap(self, p, earliest, duration):
        assert(p.index is not None)
        p_tasks = list(filter(lambda t: t.pe.index == p.index, self.tasks))
        if not p_tasks:
            return earliest
        
        p_times = [(t.t_s, t.t_f) for t in p_tasks]
        win = chain((0,0), p_times[:-1])
        for t1, t2 in zip (win, p_times):
            earliest_start = max(earliest, t2[1])
            if t2[0] - earliest_start > duration:
                return earliest_start

        return max(p_times[-1][1], earliest)

    def makespan(self):
        return max(t.t_f for t in self.tasks)


    def save_svg(self, path, m, print_locs = True):
        locations = set([task.location for task in self.tasks])
        configs = set([task.pe.configuration.index for task in self.tasks])
        PEs_count = len(m.PEs)
        left_offset = 1.2
        top_offset = 0.7
        height = PEs_count * 0.5 + (len(locations) * print_locs) * 0.5 + top_offset
        width = self.length() / 50 + left_offset
        dwg = svgwrite.Drawing(path, size=((width+0.5)*cm, (height+0.5)*cm))
        arrow = dwg.marker(id='arrow', insert=(0, 3), size=(10, 10), orient='auto', markerUnits='strokeWidth')
        arrow.add(dwg.path(d='M0,0 L0,6 L9,3 z', fill='#000'))
        dwg.defs.add(arrow)
        dwg.add(dwg.text('time', insert=((width-0.5)*cm, 0.5*cm)))
        if self.tasks[0].type:
            cmap = mpl.colormaps["Pastel1"]

        if print_locs:
            for loc in locations:
                dwg.add(dwg.text(f'$l_{loc}$', insert=(0.7*cm, (top_offset+0.35)*cm)))
                for task in self.tasks:
                    if task.location == loc:
                        task_id = task.index
                        config = task.pe.configuration
                        left = task.t_s / 50 + left_offset
                        right = task.cost / 50
                        dwg.add(dwg.rect(insert=(left*cm, (top_offset)*cm), size=(right*cm, 0.5*cm), fill='rgb(230,230,230)', stroke='rgb(200,200,200)'))
                        dwg.add(dwg.text(f'$c_{config.index}$', insert=((left + 0.2)*cm, (top_offset + 0.375)*cm)))
                top_offset = top_offset + 0.5
        line_top = top_offset



        for config in sorted(m.configurations(), key=lambda c: c.index):
            pes = len(set(pe for pe in m.PEs if pe.configuration == config))
            dwg.add(dwg.text(f'$c_{config.index}$', insert=(0.2*cm, (top_offset+((pes-1)/2*0.5)+0.4)*cm)))
            first = True
            for pe in sorted(m.PEs, key=lambda p: p.index):
                if pe.configuration != config:
                    continue
                dwg.add(dwg.text(f'$p_{pe.index}$', insert=(0.7*cm, (top_offset+0.35)*cm)))
                if first:
                    first = False
                else:
                    dwg.add(dwg.line(start=(left_offset*cm, (top_offset)*cm), end=((width)*cm, (top_offset) * cm), stroke='black').dasharray([1, 5]))
                for task in self.tasks:
                    task_id = task.index
                    if task.pe.configuration.index == config.index and task.pe.index == pe.index:
                        left = task.t_s / 50 + left_offset
                        right = task.cost / 50
                        fill = 'white'
                        if cmap:
                            fill = mpl.colors.rgb2hex(cmap(task.type))
                        dwg.add(dwg.rect(insert=(left*cm, (top_offset+0.02)*cm), size=(right*cm, 0.46*cm), stroke='black', fill=fill))
                        dwg.add(dwg.text(task.label, insert=((left + 0.2)*cm, (top_offset + 0.375)*cm)))
                        print("Task %i on PE %i: Start %i, End: %i" % (task_id, pe.index, task.t_s, task.t_f))
                top_offset = top_offset + 0.5
            dwg.add(dwg.line(start=((left_offset - 0.5)*cm, (top_offset)*cm), end=((width)*cm, (top_offset) * cm), stroke='black').dasharray([5, 5]))
        dwg.add(dwg.line(start=(left_offset*cm, line_top*cm), end=((width)*cm, line_top*cm), stroke='black'))
        dwg.add(dwg.line(start=(left_offset*cm, 0.7*cm), end=((width)*cm, 0.7*cm), stroke='black', marker_end=arrow.get_funciri()))
        dwg.add(dwg.line(start=(left_offset*cm, 0.7*cm), end=(left_offset*cm, height * cm), stroke='black'))
        makedirs(dirname(path), exist_ok = True)
        dwg.save()
