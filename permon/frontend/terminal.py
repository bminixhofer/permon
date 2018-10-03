import numpy as np
import time
import blessings
from permon.frontend import Monitor, MonitorApp, utils
import permon.backend as backend
import math


class TerminalMonitor(Monitor):
    def __init__(self, stat, buffer_size, fps, color, app,
                 resolution, axis_width=10, right_axis_width=20):
        super(TerminalMonitor, self).__init__(stat, buffer_size,
                                              fps, color, app)

        self.title = self.stat.name
        self.resolution = resolution
        self.axis_width = axis_width
        self.r_axis_width = right_axis_width
        # fill unknown history with the minimum value (or 0 if it is unknown)
        axis_space = self.axis_width + self.r_axis_width
        self.values = np.full(resolution[1] - axis_space,
                              self.stat.minimum or 0)
        self.symbols = {
            'axis': ' ┤',
            'right_axis': '├',
            'horizontal': '─',
            'vertical': '│',
            'fall_then_flat': '╰',
            'rise_then_flat': '╭',
            'flat_then_fall': '╮',
            'flat_then_rise': '╯'
        }

    def update(self):
        self.values = np.roll(self.values, -1, axis=0)

        if self.stat.has_top_info:
            value, contrib = self.stat.get_stat()
        else:
            value = self.stat.get_stat()
            contrib = {}
        self.values[-1] = value
        self.latest_contrib = contrib

    def paint(self):
        minimum = self.stat.minimum
        maximum = self.stat.maximum

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
        # and 1 to make sure the height is not exceeded
        height = self.resolution[0] - 2

        if interval > 0:
            ratio = (height - 1) / interval
        else:
            ratio = 1

        min_cell = int(np.floor(float(minimum) * ratio))
        max_cell = int(np.ceil(float(maximum) * ratio))

        rows = max(abs(max_cell - min_cell), 1)
        width = len(self.values)

        # utility function to determine which cell a value is best placed in
        def get_cell(value):
            return int(round(value * ratio) - min_cell)

        # create chart axis
        axis = []

        for y in range(rows + 1):
            label_value = float(maximum) - y * interval / rows
            axis.append(label_value)
        axis = utils.format_labels(axis)
        axis_symbol = self.symbols['axis']

        longest_label = max(len(x) for x in axis)
        pad_width = self.axis_width - len(axis_symbol)

        # create contributor axis
        contrib_axis = []

        if self.latest_contrib:
            contribs_row = [[name, value / self.stat.maximum * rows]
                            for name, value in self.latest_contrib]
            used_rows = sum(math.floor(value) for _, value in contribs_row)
            row_diff = get_cell(self.values[-1]) + 1 - used_rows
            for _ in range(row_diff):
                max_dec_index = max(enumerate(contribs_row),
                                    key=lambda x: x[1][1] % 1)[0]
                contribs_row[max_dec_index][1] = \
                    math.ceil(contribs_row[max_dec_index][1])

            for name, value in contribs_row:
                value = math.floor(value)

                contrib_axis.extend([self.symbols['vertical']] * (value - 1))
                contrib_axis.append(self.symbols['right_axis'])

                mid_index = -int(value / 2) - 1
                max_label_len = self.r_axis_width - \
                    len(contrib_axis[mid_index]) - 1

                contrib_axis[mid_index] += \
                    ' ' + utils.format_bar_label(name, max_len=max_label_len)

                if len(contrib_axis) >= get_cell(self.values[-1]) + 1:
                    break

        unused_rows = len(axis) - len(contrib_axis)
        contrib_axis.extend([self.symbols['vertical']] * unused_rows)
        contrib_axis = reversed(contrib_axis)
        contrib_axis = [x.ljust(self.r_axis_width) for x in contrib_axis]

        assert longest_label <= pad_width, 'Axis labels exceed axis width.'
        axis = [x.rjust(pad_width) + axis_symbol for x in axis]

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
        out_rows = [axis[i] +
                    self.color(''.join(line[i])) +
                    contrib_axis[i] if contrib_axis else ''
                    for i in range(rows + 1)]
        print('\n'.join(out_rows))


class TerminalApp(MonitorApp):
    def __init__(self, tags, colors, buffer_size, fps):
        super(TerminalApp, self).__init__(tags, colors, buffer_size, fps)

        self.stats = []
        for stat in backend.get_available_stats():
            if stat.get_full_tag() in tags:
                instance = stat()
                self.stats.append(instance)

    def initialize(self):
        self.term = blessings.Terminal()
        self.colors = [self.term.green, self.term.red, self.term.blue,
                       self.term.cyan, self.term.yellow]

        assert self.term.is_a_tty, \
            'Attempting to run in a non-tty environment.'
        n_charts = len(self.stats)

        # every chart can take up 1 / n_charts of the terminal space
        # use the height - 1 because the full height seems not to be usable
        # in some terminals
        height = (self.term.height - 1) // n_charts
        resolution = (height, self.term.width)

        for i, stat in enumerate(self.stats):
            monitor = TerminalMonitor(stat,
                                      buffer_size=self.buffer_size,
                                      fps=self.fps,
                                      color=self.colors[i],
                                      app=self,
                                      resolution=resolution)
            self.monitors.append(monitor)

        print(self.term.enter_fullscreen())
        print(self.term.hide_cursor())

        try:
            while True:
                self.update()
                self.paint()
                time.sleep(1 / self.fps)
        except KeyboardInterrupt:
            print(self.term.exit_fullscreen())
            # explicitly delete monitors to stop threads run by stats
            del self.monitors

    def paint(self):
        # every frame, paint all monitors and move the cursor
        # back to the start
        print(self.term.move(0, 1))
        for monitor in self.monitors:
            monitor.paint()
