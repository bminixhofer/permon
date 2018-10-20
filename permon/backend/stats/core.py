import time
import re
import threading
from collections import defaultdict
import subprocess
import warnings
import psutil
from permon.backend import Stat


class ProcessTracker():
    instance = None
    n_wrapper_instances = 0

    def __init__(self):
        if not self.instance:
            ProcessTracker.instance = self._ProcessTracker()
        ProcessTracker.n_wrapper_instances += 1

    def __del__(self):
        ProcessTracker.n_wrapper_instances -= 1
        if self.n_wrapper_instances == 0:
            self.instance._stop = True
            while not self.instance._stopped:
                continue

            ProcessTracker.instance = None

    def __getattr__(self, attr):
        return getattr(self.instance, attr)

    class _ProcessTracker():
        def __init__(self):
            self._stop = False
            self._stopped = False
            self.processes = {}
            self.contributors = defaultdict(lambda: {})

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

                used_memory = psutil.virtual_memory().used / 1000**2
                self.contributors['cpu'] = self.get_contributors('cpu')
                self.contributors['ram'] = self.get_contributors(
                    'ram', adapt_to=used_memory)
                self.processes = _processes

                # check if the thread should be stopped every 0.1 seconds
                # minimal sacrifice in performance for more responsive quitting
                for _ in range(10):
                    time.sleep(0.1)
                    if self._stop:
                        break

            self._stopped = True

        def get_contributors(self, tag, n=5, adapt_to=None):
            processes = self.processes.items()
            contributors = sorted(processes, key=lambda proc: proc[1][tag],
                                  reverse=True)
            contributors = [[key, value[tag]] for key, value in contributors]

            if adapt_to is not None:
                value_sum = max(sum(x[1] for x in contributors), 1e-6)
                for i, (_, value) in enumerate(contributors):
                    contributors[i][1] = value / value_sum * adapt_to
                remainder = adapt_to - sum(x[1] for x in contributors[:n-1])
                contributors.insert(0, ['other', remainder])
            return contributors[:n]

    def delete_instance(self):
        self.instance._stop = True
        while not self._stopped:
            continue

        self.instance = None


@Stat.windows
@Stat.linux
class CPUStat(Stat):
    name = 'CPU Usage [%]'
    base_tag = 'cpu_usage'

    def __init__(self, fps):
        self.proc_tracker = ProcessTracker()
        self.buffer = []
        self.buffer_size = 10

        super(CPUStat, self).__init__(fps=fps)

    def get_stat(self):
        cpu_percent = sum(psutil.cpu_percent(percpu=True))
        self.buffer.append(cpu_percent)
        if len(self.buffer) > self.buffer_size:
            del self.buffer[0]

        mean_percent = sum(self.buffer) / len(self.buffer)
        contributors = self.proc_tracker.get_contributors(
            'cpu', adapt_to=mean_percent)

        return mean_percent, contributors

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return 100 * psutil.cpu_count()


@Stat.windows
@Stat.linux
class RAMStat(Stat):
    name = 'RAM Usage [MB]'
    base_tag = 'ram_usage'

    def __init__(self, fps):
        self.proc_tracker = ProcessTracker()

        self._maximum = psutil.virtual_memory().total / 1000**2
        super(RAMStat, self).__init__(fps=fps)

    def get_stat(self):
        actual_memory = psutil.virtual_memory().used / 1000**2
        contributors = self.proc_tracker.contributors['ram']

        return actual_memory, contributors

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return self._maximum


@Stat.linux
class GPUStat(Stat):
    name = 'vRAM Usage [MB]'
    base_tag = 'vram_usage'

    @classmethod
    def is_available(cls):
        available = True

        try:
            subprocess.call(['nvidia-smi'])
        except OSError:
            warnings.warn('Could not display vRAM usage. '
                          'nvidia-smi not in PATH.')
            available = False

        return available

    def __init__(self, fps):
        super(GPUStat, self).__init__(fps=fps)
        self._maximum = self._get_used_and_total()[1]

    def _get_used_and_total(self):
        vram_command = ['nvidia-smi', '--display=MEMORY', '-q']

        out = subprocess.check_output(vram_command)
        out = out.decode('utf-8').split('\n')[8:]

        total = int(out[1].split()[2])
        used = int(out[2].split()[2])
        return used, total

    def get_stat(self):
        return self._get_used_and_total()[0]

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return self._maximum


@Stat.windows
@Stat.linux
class ReadStat(Stat):
    name = 'Disk Read Speed [MB / s]'
    base_tag = 'read_speed'

    def __init__(self, fps):
        self.cache = []
        self.start_bytes = psutil.disk_io_counters().read_bytes
        super(ReadStat, self).__init__(fps=fps)

    def get_stat(self):
        stat = psutil.disk_io_counters().read_bytes - self.start_bytes
        current_time = time.time()
        self.cache.append((stat, current_time))
        self.cache = [(x, t) for x, t in self.cache if current_time - t <= 1]

        return float(self.cache[-1][0] - self.cache[0][0]) / 1000**2

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return None


@Stat.windows
@Stat.linux
class WriteStat(Stat):
    name = 'Disk Write Speed [MB / s]'
    base_tag = 'write_speed'

    def __init__(self, fps):
        self.cache = []
        self.start_bytes = psutil.disk_io_counters().write_bytes
        super(WriteStat, self).__init__(fps=fps)

    def get_stat(self):
        stat = psutil.disk_io_counters().write_bytes - self.start_bytes
        current_time = time.time()
        self.cache.append((stat, current_time))
        self.cache = [(x, t) for x, t in self.cache if current_time - t <= 1]

        return float(self.cache[-1][0] - self.cache[0][0]) / 1000**2

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return None


@Stat.windows
@Stat.linux
class CPUTempStat(Stat):
    name = 'CPU Temperature [°C]'
    base_tag = 'cpu_temp'

    @classmethod
    def is_available(cls):
        if 'coretemp' in psutil.sensors_temperatures():
            return True

        warnings.warn('CPU temperature sensor could not be found.')
        return False

    def __init__(self, fps):
        critical_temps = [x.critical for x in self.get_core_temps()]
        self._maximum = sum(critical_temps) / len(critical_temps)
        super(CPUTempStat, self).__init__(fps=fps)

    def get_core_temps(self):
        return psutil.sensors_temperatures()['coretemp']

    def get_stat(self):
        core_temps = [x.current for x in self.get_core_temps()]
        return sum(core_temps) / len(core_temps)

    @property
    def minimum(self):
        return None

    @property
    def maximum(self):
        return self._maximum
