#!/usr/bin/env python
import psutil
import numpy as np
import time
import blessings
import sys
import threading
term = blessings.Terminal()
print(term.clear())
from permon.backend import get_cpu_percent, get_ram, get_vram, get_read, get_write, TOTAL_GPU, TOTAL_RAM

symbols = [u'\u2501']
fps = 7
resolution = ((term.height - 10) // 6, term.width - 20)

class Graph:
    def __init__(self, resolution, color, n_lines=1, total=None):
        self.resolution = resolution
        self.color = color
        self.total = total
        self.adaptive_total = total is None
        self.hist = np.ones((resolution[1], n_lines)) * -1

        self.charmap = np.zeros((resolution[0] + 1, resolution[1] + 1)).astype(str)
        self.charmap.fill(' ')
        if not self.adaptive_total:
            self.charmap[:, 0] = np.linspace(0, total, resolution[0] + 1).astype(int)
        self._padCharmap()

    def _padCharmap(self):
        self.charmap[1::2, 0] = ''
        self.charmap[:, 0] = [np.str.ljust(x, 10) for x in self.charmap[:, 0]]

    def step(self, value):
        self.hist = np.roll(self.hist, -1, axis=0)
        self.hist[-1] = list(value) if type(value) is tuple else [value]
        if self.adaptive_total:
            if not self.total or self.hist.max() * 2 > self.total:
                self.total = self.hist.max() * 2 if self.hist.max() * 2 > 10 else 10

                self.charmap[:, 0] = np.linspace(0, self.total, resolution[0] + 1).astype(int)
                self._padCharmap()

    def __str__(self):
        self.charmap[:, 1:].fill(' ')
        for i, values in enumerate(self.hist):
            for j, x in enumerate(values):
                if x != -1:
                    symbol = self.color[j](symbols[j])
                    y = int(x / self.total * self.resolution[0])

                    self.charmap[y, i + 1] = self.charmap[y, i + 1].replace(' ', '')
                    self.charmap[y, i + 1] = symbol
        return '\n'.join(''.join(x) for x in self.charmap.astype(str)[::-1])

try:
    cpu_graph = Graph(resolution, [term.green], total=100)
    gpu_graph = Graph(resolution, [term.red], total=TOTAL_GPU)
    ram_graph = Graph(resolution, [term.blue], total=TOTAL_RAM)
    write_graph = Graph(resolution, [term.cyan])
    read_graph = Graph(resolution, [term.yellow])

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

            time.sleep(1/fps)
except KeyboardInterrupt:
    print('Stopping..')
    print(term.clear())
    sys.exit(0)
