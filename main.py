import psutil
import numpy as np
import time
from colorama import Fore, Style, Back
import math
import subprocess
import blessings
import sys
term = blessings.Terminal()
print(term.clear())

fps = 7
resolution = (10, 100)

class Graph:
    def __init__(self, resolution, color, n_lines=1, total=None):
        self.resolution = resolution
        self.color = color
        self.total = total
        self.hist = np.ones((resolution[1], n_lines)) * -1

        self.charmap = np.zeros((resolution[0] + 1, resolution[1] + 1)).astype(str)
        self.charmap.fill(' ')
        self.charmap[:, 0] = np.linspace(0, total, resolution[0] + 1).astype(int)
        self.charmap[:, 1:2] = ''
        self.charmap[:, 0] = [np.str.ljust(x, 10) for x in self.charmap[:, 0]]

    def step(self, value):
        self.hist = np.roll(self.hist, -1)
        self.hist[-1] = list(value) if type(value) is tuple else [value]

    def __str__(self):
        self.charmap[:, 1:].fill(' ')
        for i, values in enumerate(self.hist):
            for x in values:
                if(x != -1):
                    symbol = self.color + u'\u2218' + Style.RESET_ALL
                    y = int(x / self.total * self.resolution[0])

                    self.charmap[y, i + 1] = symbol
        return '\n'.join(''.join(x) for x in self.charmap.astype(str)[::-1])


def gpustats():
    out = subprocess.check_output(['nvidia-smi', '--display=MEMORY', '-q']).decode('utf-8').split('\n')[8:]

    total = int(out[1].split()[2])
    used = int(out[2].split()[2])
    return used, total

total_ram = psutil.virtual_memory().total / 1024**2
total_gpu = gpustats()[1]

if __name__ == '__main__':
    try:
        cpu_graph = Graph(resolution, Fore.GREEN, total=100)
        gpu_graph = Graph(resolution, Fore.RED, total=total_gpu)
        ram_graph = Graph(resolution, Fore.YELLOW, total=total_ram)

        with term.hidden_cursor():
            while True:
                print(term.move(0, 1))

                print(f'{Back.GREEN}CPU Usage in Percent:{Style.RESET_ALL}')
                cpu_graph.step(psutil.cpu_percent())
                print(cpu_graph)

                print(f'{Back.RED}GPU Usage in MiB:{Style.RESET_ALL}')
                gpu_graph.step(gpustats()[0])
                print(gpu_graph)

                print(f'{Back.YELLOW}RAM Usage in MiB:{Style.RESET_ALL}')
                ram_graph.step(psutil.virtual_memory().used / 1024**2)
                print(ram_graph)

                time.sleep(1/fps)
    except KeyboardInterrupt:
        print('Stopping..')
        # print(term.clear())
        sys.exit(0)
