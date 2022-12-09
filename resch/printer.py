import svgwrite
from svgwrite import cm,mm,px
import matplotlib as mpl
from os.path import dirname
from os import makedirs
from itertools import accumulate
from functools import reduce
import schedule
import portion as po
import colorsys
from sys import stderr


# Just some horrific code to print a schedule to svg
def save_schedule(S, file, m, print_locs = True, LaTeX=False, p_height = 0.6, y_scale = 30, cmap = None):
    locations = m.locations()
    configs = m.configurations()
    pes = m.PEs
    PEs_count = len(pes)
    left_offset = 1.2
    height = PEs_count * p_height + (len(locations) * print_locs) * p_height
    width = S.length() / y_scale + left_offset
    if S.tasks[0].type and not cmap:
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

    total_bottom = (l_offsets[-1] - 1) * p_height

    dwg = svgwrite.Drawing(size=((width+0.2)*cm, (total_bottom + 0.5) * cm))
    arrow = dwg.marker(id='arrow', insert=(0, 3), size=(10, 10), orient='auto', markerUnits='strokeWidth')
    arrow.add(dwg.path(d='M0,0 L0,6 L9,3 z', fill='#000'))
    dwg.defs.add(arrow)

    for loc in locations:
        dwg.add(dwg.rect(insert=(left_offset*cm, l_offset(loc)*p_height*cm), size=((width - left_offset)*cm, p_height*cm), stroke='none', fill='rgb(250,250,250)'))
        dwg.add(dwg.text(f'{d}l_{loc.index}{d}', insert=(.3*cm, (l_offset(loc) * p_height + 0.39)*cm)))
        dwg.add(dwg.line(start=(left_offset*cm, (l_offset(loc)*p_height + p_height )*cm), end=(width*cm,  (l_offset(loc)*p_height + p_height )* cm), stroke='rgb(220,220,220)'))

        for task in S.tasks:
            if task.location == loc:

                print("Task %i on PE %i(%i)@%i: Start %i, End: %i: %s" % (task.index, task.pe.index, task.pe.configuration.index, task.instance.location.index, task.t_s, task.t_f, task.label), file=stderr)
                top = i_offset(task.instance) * p_height
                left = task.t_s / y_scale + left_offset
                right = task.cost / y_scale
                fill = 'white'
                stroke = 'black'
                if cmap:
                    fill = mpl.colors.rgb2hex(cmap(task.type))
                    r, g, b, a = cmap(task.type)
                    h, l, s = colorsys.rgb_to_hls(r, g, b)
                    stroke = mpl.colors.rgb2hex(colorsys.hls_to_rgb(h, min(1, l * 0.8), s = s))
                dwg.add(dwg.rect(insert=(left*cm, (top+0.02)*cm), size=(right*cm, p_height*cm), rx=3*px, ry=3*px, fill=fill, stroke=stroke))
                dwg.add(dwg.text(task.label, insert=((left + 0.2)*cm, (top + p_height - 0.125)*cm)))

        top = l_offset(loc) * p_height
        bottom = p_height + top + max_pes(loc) * p_height

        dwg.add(dwg.line(start=(left_offset*cm, top*cm), end=(width*cm, top * cm), stroke='rgb(150,150,150)'))

        for config in configs:
            for i in config_interval(config, loc):
                left = i.lower / y_scale + left_offset
                right = (i.upper -  i.lower) / y_scale
                fill = 'white'
                dwg.add(dwg.line(start=(left*cm, top*cm), end=(left*cm, bottom * cm), stroke='rgb(100,100,100)').dasharray([2, 2]))
                dwg.add(dwg.rect(insert=(left*cm, top*cm), size=(right*cm, p_height*cm), fill='rgb(230,230,230)', stroke='rgb(160,160,160)'))
                dwg.add(dwg.text(f'{d}c_{config.index}{d}', insert=((left + 0.2)*cm, (top + 0.375)*cm)))
            
                
    dwg.add(dwg.line(start=(left_offset*cm, 0*cm), end=(left_offset*cm, total_bottom * cm), stroke='black'))
    dwg.add(dwg.line(start=(left_offset*cm, total_bottom*cm), end=(width*cm, total_bottom * cm), stroke='black', marker_end=arrow.get_funciri()))
    # dwg.add(dwg.line(start=(left_offset*cm, total_bottom*cm), end=(width*cm, total_bottom * cm), stroke='rgb(150,150,150)'))
    dwg.add(dwg.text('time', insert=((width - 1)*cm, (0.5 + total_bottom)*cm)))
    # dwg.add(dwg.line(start=(left_offset*cm, line_top*cm), end=((width)*cm, line_top*cm), stroke='black'))
    # dwg.add(dwg.line(start=(left_offset*cm, 0.7*cm), end=((width)*cm, 0.7*cm), stroke='black', marker_end=arrow.get_funciri()))
    # dwg.add(dwg.line(start=(left_offset*cm, 0.7*cm), end=(left_offset*cm, height * cm), stroke='black'))
    # if dirname(path):
    #     makedirs(dirname(path), exist_ok = True)
    dwg.write(file)
