import time
import math
import re
import psutil
from permon.backend import Stat


@Stat.windows
@Stat.linux
class CPUStat(Stat):
    name = 'CPU Usage in %'
    tag = 'cpu_usage'

    def __init__(self):
        self._frames_without_top = math.inf
        self._fetch_top_frames = 5

        super(CPUStat, self).__init__()

    def _fetch_top(self, cpu_percent):
        processes = []
        for proc in psutil.process_iter(attrs=['name', 'cpu_percent']):
            processes.append((proc.name().split()[0],
                              proc.info['cpu_percent']))

        top = sorted(processes, key=lambda x: x[1], reverse=True)[:5]

        self.top = top

    def get_stat(self):
        cpu_percent = sum(psutil.cpu_percent(percpu=True))
        if self._frames_without_top > self._fetch_top_frames:
            self._fetch_top(cpu_percent)
            self._frames_without_top = 0

        self._frames_without_top += 1

        return cpu_percent, self.top

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return 100 * psutil.cpu_count()


@Stat.windows
@Stat.linux
class RAMStat(Stat):
    name = 'RAM Usage in MiB'
    tag = 'ram_usage'

    def __init__(self):
        self._frames_without_top = math.inf
        self._fetch_top_frames = 5

        self._maximum = psutil.virtual_memory().total / 1024**2
        super(RAMStat, self).__init__()

    def _fetch_top(self, actual_memory):
        processes = {}
        for proc in psutil.process_iter(attrs=['name', 'memory_info']):
            real_name = re.split(r'[\W\s]+', proc.name())[0]

            prev = processes[real_name] if real_name in processes else 0
            current = proc.info['memory_info'].vms / 1024**2

            processes[real_name] = prev + current

        mem_sum = sum(processes.values())
        for i, (key, value) in enumerate(processes.items()):
            processes[key] = value / mem_sum * actual_memory

        processes = sorted(processes.items(), key=lambda x: x[1], reverse=True)
        processes = processes[:5]
        top_sum = sum(x[1] for x in processes)

        processes.insert(0, ['other', actual_memory - top_sum])

        self.top = processes

    def get_stat(self):
        actual_memory = psutil.virtual_memory().used / 1024**2
        if self._frames_without_top > self._fetch_top_frames:
            self._fetch_top(actual_memory)
            self._frames_without_top = 0

        self._frames_without_top += 1

        return actual_memory, self.top

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return self._maximum


# @Stat.linux
# class GPUStat(Stat):
#     name = 'vRAM Usage in MiB'
#     tag = 'vram_usage'

#     def __init__(self):
#         self._maximum = self._get_used_and_total()[1]

#     def _get_used_and_total(self):
#         vram_command = ['nvidia-smi', '--display=MEMORY', '-q']
#         try:
#             out = subprocess.check_output(vram_command)
#             out = out.decode('utf-8').split('\n')[8:]
#         except Exception as e:
#             raise ImportError('nvidia-smi command not found.')
#         total = int(out[1].split()[2])
#         used = int(out[2].split()[2])
#         return used, total

#     def get_stat(self):
#         return self._get_used_and_total()[0]

#     @property
#     def minimum(self):
#         return 0

#     @property
#     def maximum(self):
#         return self._maximum


@Stat.windows
@Stat.linux
class ReadStat(Stat):
    name = 'Disk Read Speed in MiB / s'
    tag = 'read_speed'

    def __init__(self, fps=10):
        self.cache = []
        self.start_bytes = psutil.disk_io_counters().read_bytes
        super(ReadStat, self).__init__()

    def get_stat(self):
        stat = psutil.disk_io_counters().read_bytes - self.start_bytes
        current_time = time.time()
        self.cache.append((stat, current_time))
        self.cache = [(x, t) for x, t in self.cache if current_time - t <= 1]

        return float(self.cache[-1][0] - self.cache[0][0]) / 1024**2

    @property
    def minimum(self):
        return None

    @property
    def maximum(self):
        return None


@Stat.windows
@Stat.linux
class WriteStat(Stat):
    name = 'Disk Write Speed in MiB / s'
    tag = 'write_speed'

    def __init__(self, fps=10):
        self.cache = []
        self.start_bytes = psutil.disk_io_counters().write_bytes
        super(WriteStat, self).__init__()

    def get_stat(self):
        stat = psutil.disk_io_counters().write_bytes - self.start_bytes
        current_time = time.time()
        self.cache.append((stat, current_time))
        self.cache = [(x, t) for x, t in self.cache if current_time - t <= 1]

        return float(self.cache[-1][0] - self.cache[0][0]) / 1024**2

    @property
    def minimum(self):
        return None

    @property
    def maximum(self):
        return None
