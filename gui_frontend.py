import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import seaborn as sns
from backend import get_cpu_percent
import time
from backend import get_cpu_percent, get_ram, get_vram, get_read, get_write, TOTAL_GPU, TOTAL_RAM

matplotlib.rcParams['toolbar'] = 'None'

to_plot = [[get_cpu_percent], [get_ram], [get_vram], [get_read, get_write]]
is_adaptive = [False, False, False, True]

colors = ["#9b59b6", "#3498db", "#95a5a6", "#e74c3c", "#34495e", "#2ecc71"]
n = 300
x = np.arange(n)
n_metrics = sum(len(x) for x in to_plot)
y = np.ones((n, n_metrics)) * -1

fig, ax = plt.subplots(nrows=len(to_plot))
plt.subplots_adjust(hspace=0.4)


# CPU Graph
ax[0].set_ylim([0, 100])
ax[0].set_title('CPU Usage', loc='left')
# RAM Graph
ax[1].set_ylim([0, TOTAL_RAM])
ax[1].set_title('RAM Usage', loc='left')
# GPU Graph
ax[2].set_ylim([0, TOTAL_GPU])
ax[2].set_title('vRAM Usage', loc='left')
# Read / Write Graph
ax[3].set_title('Read / Write Speed', loc='left')

lines = []
for i, axis in enumerate(ax):
    axis.get_xaxis().set_ticks([])
    axis.set_xlim([0, n])

    axis_lines = []
    for _ in range(len(to_plot[i])):
        line = axis.plot(x, y[:, 0], color=colors[i])[0]
        axis_lines.append(line)
    lines.append(axis_lines)


def update(num, lines):
    global x, y, fig

    y = np.roll(y, -1, axis=0)

    index = 0
    ticks = []
    for n_line, value_list in enumerate(num):
        mx = 0
        for i, val in enumerate(value_list):
            y[-1, index] = val
            lines[n_line][i].set_data(x, y[:, index])

            mx = max(mx, y[:, index].max())
            index += 1

        if is_adaptive[n_line]:
            ax = lines[n_line][0].axes
            if mx * 2 != ax.get_ylim[1]:
                ax.set_ylim([0, mx * 2])
                fig.canvas.draw()

    return [line for sublist in lines for line in sublist]

def generator(funcs):
    while True:
        results = []
        for func in funcs:
            try:
                results.append([f() for f in func])
            except:
                results.append([-1])
        yield results


ani = animation.FuncAnimation(fig, update, generator(to_plot), fargs=[lines], interval=100, repeat=False, blit=True)
plt.show()
