import time
import psutil
from permon.backend import Stat


@Stat.windows
@Stat.linux
class CPUStat(Stat):
    name = 'CPU Usage in %'
    tag = 'cpu_usage'

    def get_stat(self):
        return psutil.cpu_percent()

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return 100


@Stat.windows
@Stat.linux
class RAMStat(Stat):
    name = 'RAM Usage in MiB'
    tag = 'ram_usage'

    def __init__(self):
        self._maximum = psutil.virtual_memory().total / 1024**2

    def get_stat(self):
        return psutil.virtual_memory().used / 1024**2

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
