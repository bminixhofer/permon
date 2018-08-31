import numpy as np
import time
import blessings
import sys
from permon.classes import Monitor, MonitorApp


def format_labels(axis_values):
    max_value = abs(max(axis_values))

    def format_value(x):
        if max_value <= 10:
            return '{:.3f}'.format(x)
        elif max_value <= 100:
            return '{:.2f}'.format(x)
        elif max_value <= 1000:
            return '{:.1f}'.format(x)
        elif max_value <= 10000:
            return str(int(x / 50) * 50)
        elif max_value > 10000:
            return str(int(x / 100) * 100)

    return [format_value(x) for x in axis_values]


class TerminalMonitor(Monitor):
    def __init__(self, stat_func, title, buffer_size, fps, color, resolution,
                 minimum=None, maximum=None):
        super(TerminalMonitor, self).__init__(stat_func, title, buffer_size,
                                              fps, color, minimum=minimum,
                                              maximum=maximum)

        self.title = title
        self.resolution = resolution
        self.values = np.full(resolution[1], self.minimum or 0)
        self.symbols = {
            'horizontal': '─',
            'vertical': '│',
            'fall_then_flat': '╰',
            'rise_then_flat': '╭',
            'flat_then_fall': '╮',
            'flat_then_rise': '╯'
        }
        # apply color to symbols
        for key, symbol in self.symbols.items():
            self.symbols[key] = self.color(symbol)

    def update(self):
        self.values = np.roll(self.values, -1, axis=0)
        self.values[-1] = self.stat_func()

    def paint(self):
        minimum = self.minimum
        maximum = self.maximum

        range_is_zero = np.max(self.values) == np.min(self.values)
        if minimum is None:
            if range_is_zero:
                minimum = -1
            else:
                minimum = min(self.values)
        if maximum is None:
            if range_is_zero:
                maximum = 1
            else:
                maximum = max(self.values)

        interval = float(abs(maximum - minimum))
        height = self.resolution[0]

        if interval > 0:
            ratio = height / interval
        else:
            ratio = 1

        min_cell = int(np.floor(float(minimum) * ratio))
        max_cell = int(np.ceil(float(maximum) * ratio))

        rows = max(abs(max_cell - min_cell), 1)
        width = len(self.values)

        line = [[' '] * width for i in range(rows + 1)]
        axis = []

        for y in range(rows + 1):
            label_value = float(maximum) - y * interval / rows
            axis.append(label_value)
        axis = format_labels(axis)
        axis = [x.rjust(7) + ' ┤' for x in axis]

        def get_cell(value):
            return int(round(value * ratio) - min_cell)

        for x in range(0, len(self.values) - 1):  # plot the line
            value = get_cell(self.values[x])
            next_value = get_cell(self.values[x + 1])

            if value == next_value:
                line[rows - value][x] = self.symbols['horizontal']
            else:
                if value > next_value:
                    line[rows - next_value][x] = self.symbols['fall_then_flat']
                    line[rows - value][x] = self.symbols['flat_then_fall']
                else:
                    line[rows - next_value][x] = self.symbols['rise_then_flat']
                    line[rows - value][x] = self.symbols['flat_then_rise']

                start = min(value, next_value) + 1
                end = max(value, next_value)
                for y in range(start, end):
                    line[rows - y][x] = self.symbols['vertical']

        print(self.color(self.title))
        print('\n'.join(axis[i] + ''.join(line[i]) for i in range(rows + 1)))


class TerminalApp(MonitorApp):
    def initialize(self):
        self.term = blessings.Terminal()
        self.colors = [self.term.green, self.term.red, self.term.blue,
                       self.term.cyan, self.term.yellow]

        chart_padding = 15
        n_charts = len(self.stat_funcs)

        # each chart needs 2 lines (title + 1 blank line)
        height = (self.term.height - n_charts * 2) // n_charts - 1
        resolution = (height, self.term.width - chart_padding)

        for i, (func, info) in enumerate(self.stat_funcs):
            monitor = TerminalMonitor(func, info['title'],
                                      buffer_size=self.buffer_size,
                                      fps=self.fps,
                                      color=self.colors[i],
                                      resolution=resolution,
                                      minimum=info['minimum'],
                                      maximum=info['maximum'])
            self.monitors.append(monitor)

        print(self.term.enter_fullscreen())
        print(self.term.hide_cursor())

        try:
            while True:
                self.update()
                self.paint()
                time.sleep(1 / self.fps)
        finally:
            print('Stopping..')
            print(self.term.exit_fullscreen())
            sys.exit(0)

    def paint(self):
        print(self.term.move(0, 1))
        for monitor in self.monitors:
            monitor.paint()
