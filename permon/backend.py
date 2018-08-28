import psutil
import threading
import subprocess
from subprocess import Popen, PIPE

read_write = (0, 0)


def gpustats():
    vram_command = ['nvidia-smi', '--display=MEMORY', '-q']
    try:
        out = subprocess.check_output(vram_command).decode('utf-8').split('\n')
        out = out[8:]
    except Exception as e:
        raise ImportError('nvidia-smi command not found.')
    total = int(out[1].split()[2])
    used = int(out[2].split()[2])
    return used, total


def worker():
    global read_write
    p = Popen('iostat -m 1 -g ALL -H'.split(), stdout=PIPE, stderr=PIPE)
    for line in p.stdout:
        line = line.decode('utf-8')
        if line.strip().startswith('ALL'):
            read_write = line.split()[2:4]
            # replace , with . to be convert the string to a number
            read_write = tuple(float(x.replace(',', '.')) for x in read_write)


t = threading.Thread(target=worker)
t.start()


def get_cpu_percent():
    return psutil.cpu_percent()


def get_ram():
    return psutil.virtual_memory().used / 1024**2


def get_vram():
    return gpustats()[0]


def get_read():
    return read_write[0]


def get_write():
    return read_write[1]


TOTAL_RAM = psutil.virtual_memory().total / 1024**2
TOTAL_GPU = None
try:
    TOTAL_GPU = gpustats()[1]
except Exception as e:
    print('GPU unavailable.')
