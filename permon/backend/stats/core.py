import time
import re
import threading
from collections import defaultdict
import psutil
from permon.backend import Stat


class ProcessTracker():
    instance = None
    n_wrapper_instances = 0

    class __ProcessTracker():
        def __init__(self):
            self._stop = False
            self._stopped = False
            self.processes = {}
            self.n_top = defaultdict(lambda: {})

            self._thread = threading.Thread(target=self._read_processes)
            self._thread.start()

        def _read_processes(self):
            while not self._stop:
                iterator = psutil.process_iter()
                _processes = {}

                for proc in iterator:
                    name = re.split(r'[\W\s]+', proc.name())[0]
                    if name not in _processes:
                        _processes[name] = {
                            'cpu': proc.cpu_percent(),
                            'ram': proc.memory_info().vms
                        }
                    else:
                        _processes[name]['cpu'] += proc.cpu_percent()
                        _processes[name]['ram'] += proc.memory_info().vms

                used_memory = psutil.virtual_memory().used / 1024**2
                self.n_top['cpu'] = self.get_n_top('cpu')
                self.n_top['ram'] = self.get_n_top('ram', adapt_to=used_memory)
                self.processes = _processes
                time.sleep(1)

            self._stopped = True

        def get_n_top(self, tag, n=5, adapt_to=None):
            processes = self.processes.items()
            top = sorted(processes, key=lambda proc: proc[1][tag],
                         reverse=True)
            top = [[key, value[tag]] for key, value in top]

            if adapt_to is not None:
                value_sum = max(sum(x[1] for x in top), 1e-6)
                for i, (_, value) in enumerate(top):
                    top[i][1] = value / value_sum * adapt_to
                remainder = adapt_to - sum(x[1] for x in top[:n-1])
                top.insert(0, ['other', remainder])
            return top[:n]

    def __init__(self):
        if not self.instance:
            ProcessTracker.instance = self.__ProcessTracker()
        ProcessTracker.n_wrapper_instances += 1

    def __del__(self):
        ProcessTracker.n_wrapper_instances -= 1
        if self.n_wrapper_instances == 0:
            self.instance._stop = True
            while not self.instance._stopped:
                continue

            ProcessTracker.instance = None

    def delete_instance(self):
        self.instance._stop = True
        while not self._stopped:
            continue

        self.instance = None

    def __getattr__(self, attr):
        return getattr(self.instance, attr)


@Stat.windows
@Stat.linux
class CPUStat(Stat):
    name = 'CPU Usage in %'
    tag = 'cpu_usage'

    def __init__(self):
        self.proc_tracker = ProcessTracker()
        self.buffer = []
        self.buffer_size = 10

        super(CPUStat, self).__init__()

    def get_stat(self):
        cpu_percent = sum(psutil.cpu_percent(percpu=True))
        self.buffer.append(cpu_percent)
        if len(self.buffer) > self.buffer_size:
            del self.buffer[0]

        mean_percent = sum(self.buffer) / len(self.buffer)
        top = self.proc_tracker.n_top['cpu']

        return mean_percent, top

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
        self.proc_tracker = ProcessTracker()

        self._maximum = psutil.virtual_memory().total / 1024**2
        super(RAMStat, self).__init__()

    def get_stat(self):
        actual_memory = psutil.virtual_memory().used / 1024**2
        top = self.proc_tracker.n_top['ram']

        return actual_memory, top

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
        return 0

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
        return 0

    @property
    def maximum(self):
        return None
