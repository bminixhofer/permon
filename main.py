import psutil
import numpy as np
import time
from colorama import Fore, Style, Back
import math
import subprocess
import blessings
import sys
term = blessings.Terminal()

def gpustats():
    out = subprocess.check_output(['nvidia-smi', '--display=MEMORY', '-q']).decode('utf-8').split('\n')[8:]

    total = int(out[1].split()[2])
    used = int(out[2].split()[2])
    return used, total

res = (term.height // 4, term.width - 10)
pad = 5

cpu_hist = np.ones(res[1]) * -1
ram_hist = np.ones(res[1]) * -1
gpu_hist = np.ones(res[1]) * -1

total_ram = math.ceil(psutil.virtual_memory().total / 1024**3) * 1024
total_gpu = math.ceil(gpustats()[1] / 1024) * 1024

def plot(out, color, axis):
    output = np.zeros((res[0] + 1, res[1] + 1)).astype(str)
    output[:] = ' '

    output[:, 0] = axis

    for i, x in enumerate(out):
        if(x != -1):
            output[int(x * res[0]), i + 1] = color + u'\u2218' + Style.RESET_ALL

    print('\n'.join(''.join(x) for x in output.astype(str)[::-1]))

def show_graphs():
    with term.location(0, 1):
        print(f'{Back.GREEN}CPU Usage in Percent:{Style.RESET_ALL}')

        cpu_axis = np.array([str(x * int((100 / res[0]))) for x in range(res[0] + 1)])
        cpu_axis[1::2] = ''
        cpu_axis = [np.str.ljust(x, 10) for x in cpu_axis]

        plot(cpu_hist, Fore.GREEN, cpu_axis)
    with term.location(0, res[0] + pad):
        print(f'{Back.BLUE}RAM Usage in MiB:{Style.RESET_ALL}')
        ram_axis = np.arange(0, total_ram, total_ram // res[0]).astype(str)
        ram_axis[1::2] = ''
        ram_axis = [np.str.ljust(x, 10) for x in ram_axis]

        plot(ram_hist, Fore.BLUE, ram_axis)
    with term.location(0, (res[0] + pad) * 2):
        print(f'{Back.RED}GPU RAM Usage in MiB:{Style.RESET_ALL}')
        gpu_axis = np.arange(0, total_gpu, total_gpu // res[0]).astype(str)
        gpu_axis[1::2] = ''
        gpu_axis = [np.str.ljust(x, 10) for x in gpu_axis]

        plot(gpu_hist, Fore.RED, gpu_axis)

prevdiskio = psutil.disk_io_counters()
if __name__ == '__main__':
    try:
        while True:
            cpu_hist = np.roll(cpu_hist, -1)
            cpu_hist[-1] = psutil.cpu_percent() / 100

            ram_hist = np.roll(ram_hist, -1)
            ram_hist[-1] = (psutil.virtual_memory().used / 1024**2) / total_ram

            gpu_hist = np.roll(gpu_hist, -1)
            gpu_hist[-1] = gpustats()[0] / total_gpu

            diskio = psutil.disk_io_counters()
            read_bytes = diskio.read_bytes - prevdiskio.read_bytes
            write_bytes = diskio.write_bytes - prevdiskio.write_bytes
            prevdiskio = diskio


            show_graphs()
            time.sleep(1/10)
    except KeyboardInterrupt:
        print('Stopping..')
        print(term.clear())
        sys.exit(0)
