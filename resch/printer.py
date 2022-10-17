import svgwrite
from svgwrite import cm,mm,px
import matplotlib as mpl
from os.path import dirname
from os import makedirs
from itertools import accumulate
from functools import reduce
from resch import schedule
import portion as po


# Just some horrific code to print a schedule to svg
def save_schedule(S, path, m, print_locs = True, LaTeX=False):
    locations = m.locations()
    configs = m.configurations()
    pes = m.PEs
    PEs_count = len(pes)
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
    l_pes = [1] 
    for loc in locations:
        l_pes.append(max_pes(loc) + 1)
    l_offsets = list(accumulate(l_pes))

    def i_offset(i):
        sorted_pes = sorted(i.config.PEs, key = lambda p : p.index)
        return l_offsets[i.location.index] + sorted_pes.index(i.pe)
    
    def l_offset(l):
        return l_offsets[l.index] - 1

    def merged_configs(l):
        ordered_tasks = sorted([task for task in S.tasks if task.location == l], key = lambda t: t.t_s)

        merged = []
        current = ordered_tasks[0]
        for task in ordered_tasks:
            if current.pe.configuration == task.pe.configuration:
                current.t_f = task.t_f
            else:
                merged.append(current)
                current = task
        return merged

    def config_interval(config, loc):
        return reduce(lambda l, r: l | r, [t.interval for t in S.tasks if t.pe.configuration == config and t.instance.location == loc], po.empty())

    d = '$' if LaTeX else  ''

    total_bottom = (l_offsets[-1] - 1) * 0.5


    for loc in locations:
        dwg.add(dwg.rect(insert=(left_offset*cm, l_offset(loc)*0.5*cm), size=((width - left_offset)*cm, 0.5*cm), stroke='none', fill='rgb(250,250,250)'))
        dwg.add(dwg.text(f'{d}l_{loc.index}{d}', insert=(.3*cm, (l_offset(loc) * 0.5 + 0.39)*cm)))
        dwg.add(dwg.line(start=(left_offset*cm, (l_offset(loc)*0.5 + 0.5 )*cm), end=(width*cm,  (l_offset(loc)*0.5 + 0.5 )* cm), stroke='rgb(220,220,220)'))

        for task in S.tasks:
            if task.location == loc:

                print("Task %i on PE %i(%i)@%i: Start %i, End: %i: %s" % (task.index, task.pe.index, task.pe.configuration.index, task.instance.location.index, task.t_s, task.t_f, task.label))
                top = i_offset(task.instance) * 0.5
                left = task.t_s / 50 + left_offset
                right = task.cost / 50
                fill = 'white'
                if cmap:
                    fill = mpl.colors.rgb2hex(cmap(task.type))
                dwg.add(dwg.rect(insert=(left*cm, (top+0.02)*cm), size=(right*cm, 0.46*cm), rx=2*px, ry=2*px, fill=fill))
                dwg.add(dwg.text(task.label, insert=((left + 0.2)*cm, (top + 0.375)*cm)))

        top = l_offset(loc) * 0.5
        bottom = (top + max_pes(loc) * 0.5)

        dwg.add(dwg.line(start=(left_offset*cm, top*cm), end=(width*cm, top * cm), stroke='rgb(150,150,150)'))

        for config in configs:
            for i in config_interval(config, loc):
                left = i.lower / 50 + left_offset
                right = (i.upper -  i.lower) / 50
                fill = 'white'
                dwg.add(dwg.line(start=(left*cm, top*cm), end=(left*cm, bottom * cm), stroke='rgb(100,100,100)').dasharray([2, 2]))
                dwg.add(dwg.rect(insert=(left*cm, top*cm), size=(right*cm, 0.5*cm), fill='rgb(230,230,230)', stroke='rgb(160,160,160)'))
                dwg.add(dwg.text(f'{d}c_{config.index}{d}', insert=((left + 0.2)*cm, (top + 0.375)*cm)))
            
                
    dwg.add(dwg.line(start=(left_offset*cm, top_offset*cm), end=(left_offset*cm, total_bottom * cm), stroke='black'))
    dwg.add(dwg.line(start=(left_offset*cm, total_bottom*cm), end=(width*cm, total_bottom * cm), stroke='rgb(150,150,150)'))
    # dwg.add(dwg.line(start=(left_offset*cm, line_top*cm), end=((width)*cm, line_top*cm), stroke='black'))
    # dwg.add(dwg.line(start=(left_offset*cm, 0.7*cm), end=((width)*cm, 0.7*cm), stroke='black', marker_end=arrow.get_funciri()))
    # dwg.add(dwg.line(start=(left_offset*cm, 0.7*cm), end=(left_offset*cm, height * cm), stroke='black'))
    makedirs(dirname(path), exist_ok = True)
    dwg.save()
