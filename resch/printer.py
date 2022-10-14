import svgwrite
from svgwrite import cm,mm
import matplotlib as mpl
from os.path import dirname
from os import makedirs
from itertools import accumulate

def save_schedule(S, path, m, print_locs = True, LaTeX=False):
    locations = set([task.location for task in S.tasks])
    configs = set([task.pe.configuration.index for task in S.tasks])
    PEs_count = len(m.PEs)
    left_offset = 1.2
    top_offset = 0.7
    height = PEs_count * 0.5 + (len(locations) * print_locs) * 0.5 + top_offset
    width = S.length() / 50 + left_offset
    dwg = svgwrite.Drawing(path, size=((width+0.5)*cm, (height+0.5)*cm))
    arrow = dwg.marker(id='arrow', insert=(0, 3), size=(10, 10), orient='auto', markerUnits='strokeWidth')
    arrow.add(dwg.path(d='M0,0 L0,6 L9,3 z', fill='#000'))
    dwg.defs.add(arrow)
    dwg.add(dwg.text('time', insert=((width-0.5)*cm, 0.5*cm)))
    if S.tasks[0].type:
        cmap = mpl.colormaps["Pastel1"]

    max_pes = lambda l : max([len(c.PEs) for c in m.configurations() if l in c.locations])
    l_pes = [0] 
    for loc in locations:
        l_pes.append(max_pes(loc) + 1)
    l_offsets = list(accumulate(l_pes))
    # TODO: here
    i_offsets = list(l_offset[i.location.index] for _,  in )

    d = '$' if LaTeX else  ''
    for loc in locations:
        dwg.add(dwg.text(f'{d}l_{loc.index}{d}', insert=(0.7*cm, (top_offset+0.35)*cm)))
        for task in S.tasks:
            if task.location == loc:
                task_id = task.index
                config = task.pe.configuration
                left = task.t_s / 50 + left_offset
                right = task.cost / 50
                dwg.add(dwg.rect(insert=(left*cm, (top_offset)*cm), size=(right*cm, 0.5*cm), fill='rgb(230,230,230)', stroke='rgb(200,200,200)'))
                dwg.add(dwg.text(f'{d}c_{config.index}{d}', insert=((left + 0.2)*cm, (top_offset + 0.375)*cm)))
        top_offset = top_offset + 0.5
    line_top = top_offset


    for config in sorted(m.configurations(), key=lambda c: c.index):
        pes = len(set(pe for pe in m.PEs if pe.configuration == config))
        dwg.add(dwg.text(f'{d}c_{config.index}{d}', insert=(0.2*cm, (top_offset+((pes-1)/2*0.5)+0.4)*cm)))
        first = True
        for pe in sorted(m.PEs, key=lambda p: p.index):
            if pe.configuration != config:
                continue
            dwg.add(dwg.text(f'{d}p_{pe.index}{d}', insert=(0.7*cm, (top_offset+0.35)*cm)))
            if first:
                first = False
            else:
                dwg.add(dwg.line(start=(left_offset*cm, (top_offset)*cm), end=((width)*cm, (top_offset) * cm), stroke='black').dasharray([1, 5]))
            for task in S.tasks:
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
