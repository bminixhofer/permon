import psutil
import bitmath
import numpy as np
import time
from colorama import Fore, Style, Back
import math


res = (15, 50)
cpu_hist = np.ones(res[1]) * -1
ram_hist = np.ones(res[1]) * -1
total_ram = math.ceil(psutil.virtual_memory().total / 1024**3) * 1024

def plot(out, color, axis):
    output = np.zeros((res[0] + 1, res[1] + 1)).astype(str)
    output[:] = ' '

    output[:, 0] = axis

    for i, x in enumerate(out):
        if(x != -1):
            output[int(x * res[0]), i + 1] = color + u'\u2218' + Style.RESET_ALL

    print('\n'.join(''.join(x) for x in output.astype(str)[::-1]))

def show_graphs():
    print(chr(27) + "[2J")
    print(f'{Back.GREEN}CPU Usage in Percent:{Style.RESET_ALL}')

    cpu_axis = np.array([str(x * int((100 / res[0]))) for x in range(res[0] + 1)])
    cpu_axis[1::2] = ''
    cpu_axis = [np.str.ljust(x, 10) for x in cpu_axis]

    plot(cpu_hist, Fore.GREEN, cpu_axis)

    print(f'{Back.BLUE}RAM Usage in MiB:{Style.RESET_ALL}')
    ram_axis = np.arange(0, total_ram, total_ram // res[0]).astype(str)
    ram_axis[1::2] = ''
    ram_axis = [np.str.ljust(x, 10) for x in ram_axis]

    plot(ram_hist, Fore.BLUE, ram_axis)



while True:
    cpu_hist = np.roll(cpu_hist, -1)
    cpu_hist[-1] = psutil.cpu_percent() / 100

    ram_hist = np.roll(ram_hist, -1)
    ram = psutil.virtual_memory()
    ram_hist[-1] = (ram.used / 1024**2) / total_ram
    show_graphs()
    time.sleep(1/10)
