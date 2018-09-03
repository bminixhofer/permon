import numpy as np
import time
import blessings
import sys
from permon.classes import Monitor, MonitorApp
from permon.frontend import utils


class TerminalMonitor(Monitor):
    def __init__(self, stat_func, title, buffer_size, fps, color, resolution,
                 minimum=None, maximum=None, axis_width=10):
        super(TerminalMonitor, self).__init__(stat_func, title, buffer_size,
                                              fps, color, minimum=minimum,
                                              maximum=maximum)

        self.title = title
        self.resolution = resolution
        self.axis_width = axis_width
        # fill unknown history with the minimum value
        self.values = np.full(resolution[1] - self.axis_width,
                              self.minimum or 0)
        self.symbols = {
            'axis': ' ┤',
            'horizontal': '─',
            'vertical': '│',
            'fall_then_flat': '╰',
            'rise_then_flat': '╭',
            'flat_then_fall': '╮',
            'flat_then_rise': '╯'
        }

    def update(self):
        self.values = np.roll(self.values, -1, axis=0)
        self.values[-1] = self.stat_func()

    def paint(self):
        minimum = self.minimum
        maximum = self.maximum

        # if we dont know the min or max and they cant be determined by
        # the history, we have to set some defaults (e. g. -1 and 1)
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
        # we have to reserve 1 line for the chart title
        height = self.resolution[0] - 1

        if interval > 0:
            ratio = (height - 1) / interval
        else:
            ratio = 1

        min_cell = int(np.floor(float(minimum) * ratio))
        max_cell = int(np.ceil(float(maximum) * ratio))

        rows = max(abs(max_cell - min_cell), 1)
        width = len(self.values)

        # create chart axis
        axis = []

        for y in range(rows + 1):
            label_value = float(maximum) - y * interval / rows
            axis.append(label_value)
        axis = utils.format_labels(axis)
        axis_symbol = self.symbols['axis']

        longest_label = max(len(x) for x in axis)
        pad_width = self.axis_width - len(axis_symbol)

        assert longest_label <= pad_width, 'Axis labels exceed axis width.'
        axis = [x.rjust(pad_width) + axis_symbol
                for x in axis]

        # utility function to determine which cell a value is best placed in
        def get_cell(value):
            return int(round(value * ratio) - min_cell)

        # create chart line
        line = [[' '] * width for i in range(rows + 1)]

        for x in range(0, len(self.values) - 1):
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

        # title and line have the chart color, while the axis is always white
        print(self.color(self.title))
        print('\n'.join(axis[i] +
              self.color(''.join(line[i])) for i in range(rows + 1)))


class TerminalApp(MonitorApp):
    def __init__(self, stat_funcs, colors, buffer_size, fps):
        super(TerminalApp, self).__init__(stat_funcs, colors, buffer_size, fps)
        self.term = blessings.Terminal()
        self.colors = [self.term.green, self.term.red, self.term.blue,
                       self.term.cyan, self.term.yellow]

    def initialize(self):
        assert self.term.is_a_tty, \
            'Attempting to run in a non-tty environment.'
        n_charts = len(self.stat_funcs)

        # every chart can take up 1 / n_charts of the terminal space
        # use the height - 1 because the full height seems not to be usable
        # in some terminals
        height = (self.term.height - 1) // n_charts
        resolution = (height, self.term.width)

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
        # every frame, paint all monitors and move the cursor
        # back to the start
        print(self.term.move(0, 1))
        for monitor in self.monitors:
            monitor.paint()
