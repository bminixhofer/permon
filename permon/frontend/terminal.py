import numpy as np
import time
import blessings
import sys


class Graph:
    def __init__(self, resolution, color, format_fn=lambda x: np.round(x, 2),
                 minimum=None, maximum=None):
        if minimum and maximum:
            assert np.abs(maximum - minimum) > 0, \
                'Graph range must be greater than zero.'

        self.resolution = resolution
        self.color = color
        self.format_fn = format_fn
        self.minimum = minimum
        self.maximum = maximum
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
            self.symbols[key] = color(symbol)

    def step(self, value):
        self.values = np.roll(self.values, -1, axis=0)
        self.values[-1] = value

    def __str__(self):
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
            label = str(self.format_fn(label_value)).rjust(5)
            axis.append(label + ' ┤')

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

        return '\n'.join(axis[i] + ''.join(line[i]) for i in range(rows + 1))


def round_pre_comma(x, precision):
    return int(x / precision) * precision


def main():
    term = blessings.Terminal()
    print(term.enter_fullscreen())
    from permon.backend import get_cpu_percent, get_ram, get_vram, get_read, \
        get_write, TOTAL_GPU, TOTAL_RAM

    fps = 7
    padding = 15
    n_charts = 5

    # each chart needs 2 lines (title + 1 blank line)
    height = (term.height - n_charts * 2) // n_charts
    resolution = (height, term.width - padding)

    try:
        cpu_graph = Graph(resolution, term.green, minimum=0, maximum=100,
                          format_fn=lambda x: int(x))
        gpu_graph = Graph(resolution, term.red, minimum=0, maximum=TOTAL_GPU,
                          format_fn=lambda x: round_pre_comma(x, 100))
        ram_graph = Graph(resolution, term.blue, minimum=0, maximum=TOTAL_RAM,
                          format_fn=lambda x: int(x / 100) * 100)
        write_graph = Graph(resolution, term.cyan, minimum=0)
        read_graph = Graph(resolution, term.yellow, minimum=0)

        with term.hidden_cursor():
            while True:
                print(term.move(0, 1))

                cpu_graph.step(get_cpu_percent())
                print(term.on_green('CPU Usage in Percent:'))
                print(cpu_graph)

                try:
                    gpu_graph.step(get_vram())
                    print()
                    print(term.on_red('GPU Usage in MiB:'))
                    print(gpu_graph)
                except Exception as e:
                    print(term.on_red(str(e)))

                ram_graph.step(get_ram())
                print()
                print(term.on_blue('RAM Usage in MiB:'))
                print(ram_graph)

                try:
                    read_graph.step(get_read())
                    print()
                    print(term.on_yellow('Read Speed in MiB per Second:'))
                    print(read_graph)
                except Exception as e:
                    raise e
                    print(term.on_yellow(str(e)))

                try:
                    write_graph.step(get_write())
                    print()
                    print(term.on_cyan('Write Speed in MiB per Second:'))
                    print(write_graph)
                except Exception as e:
                    raise e
                    print(term.on_cyan(str(e)))

                time.sleep(1 / fps)
    except KeyboardInterrupt:
        print('Stopping..')
        print(term.exit_fullscreen())
        sys.exit(0)
