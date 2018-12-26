import time
import re
import threading
import subprocess
import psutil
from permon.backend import Stat
from permon import exceptions


class CPUStat(Stat):
    """
    tag: ``core.cpu_usage``

    settings: none

    Tracks the CPU usage of the user.
    Also returns the top contributors to the CPU usage.
    """
    name = 'CPU Usage [%]'
    base_tag = 'cpu_usage'

    def __init__(self, fps):
        # get a new wrapper around the process tracker singleton
        self.proc_tracker = ProcessTracker()

        super(CPUStat, self).__init__(fps=fps)

    def get_stat(self):
        # get the sum of all CPU cores.
        cpu_percent = sum(psutil.cpu_percent(percpu=True))
        # get the top contributors to CPU usage from the process tracker
        contributors = self.proc_tracker.get_contributors(
            'cpu', adapt_to=cpu_percent)

        return cpu_percent, contributors

    @property
    def minimum(self):
        # the minimum cpu usage is (theoretically) 0
        return 0

    @property
    def maximum(self):
        # display the maximum as 100% * the number of cores
        return 100 * psutil.cpu_count()


class RAMStat(Stat):
    """
    tag: ``core.ram_usage``

    settings: none

    Tracks the RAM usage of the user.
    Also returns the top contributors to the RAM usage.
    """
    name = 'RAM Usage [MB]'
    base_tag = 'ram_usage'

    def __init__(self, fps):
        # get a new wrapper around the process tracker singleton
        self.proc_tracker = ProcessTracker()

        # calculate the maximum in MB, psutil returns bytes
        self._maximum = psutil.virtual_memory().total / 1000**2
        super(RAMStat, self).__init__(fps=fps)

    def get_stat(self):
        # get the currently used memory from psutil
        actual_memory = psutil.virtual_memory().used / 1000**2
        # get the contributors from the process tracker
        contributors = self.proc_tracker.get_contributors(
            'ram', adapt_to=actual_memory)

        return actual_memory, contributors

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return self._maximum


class GPUStat(Stat):
    """
    tag: ``core.vram_usage``

    settings: none

    Tracks the current vRAM usage of the user.
    Currently only works for NVIDIA GPUs and ``nvidia-smi``
    must be installed. To check if it is installed, type ``nvidia-smi``
    in your command line and see if the command was found.

    """
    name = 'vRAM Usage [MB]'
    base_tag = 'vram_usage'

    @classmethod
    def check_availability(cls):
        """
        Attempt to find `nvidia-smi`.
        GPU usage only works on NVIDIA GPUs and only when
        `nvidia-smi` is installed.
        """
        status, message = subprocess.getstatusoutput('nvidia-smi')
        if status != 0:
            raise exceptions.StatNotAvailableError(message)

    def __init__(self, fps):
        super(GPUStat, self).__init__(fps=fps)
        self._maximum = self._get_used_and_total()[1]

    def _get_used_and_total(self):
        """
        Extract and return the used and total vRAM, respectively
        from nvidia-smi.
        """
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


class ReadStat(Stat):
    """
    tag: ``core.read_speed``

    settings: none

    Tracks the disk read speed of the user.
    """
    name = 'Disk Read Speed [MB / s]'
    base_tag = 'read_speed'

    def __init__(self, fps):
        self.cache = []
        # start_bytes is equal to the number of bytes that have been
        # read since startup
        self.start_bytes = psutil.disk_io_counters().read_bytes
        super(ReadStat, self).__init__(fps=fps)

    def get_stat(self):
        # subtract the read bytes since startup from the
        # bytes that have been read before permon has been started
        stat = psutil.disk_io_counters().read_bytes - self.start_bytes
        current_time = time.time()
        # append the difference in bytes and the current time to a cache
        self.cache.append((stat, current_time))
        # remove all entries from the cache that are older than 1 second
        self.cache = [(x, t) for x, t in self.cache if current_time - t <= 1]

        # return the difference between the last and first entry of the cache
        # this is equal to the bytes read since the last second
        return float(self.cache[-1][0] - self.cache[0][0]) / 1000**2

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        # the maximum is not known beforehand, so make it adaptive
        return None


class WriteStat(Stat):
    """
    tag: ``core.write_speed``

    settings: none

    Tracks the disk write speed of the user.
    """
    name = 'Disk Write Speed [MB / s]'
    base_tag = 'write_speed'

    def __init__(self, fps):
        self.cache = []
        # start_bytes is equal to the number of bytes that have been
        # written since startup
        self.start_bytes = psutil.disk_io_counters().write_bytes
        super(WriteStat, self).__init__(fps=fps)

    def get_stat(self):
        # subtract the written bytes since startup from the
        # bytes that have been written before permon has been started
        stat = psutil.disk_io_counters().write_bytes - self.start_bytes
        current_time = time.time()
        # append the difference in bytes and the current time to a cache
        self.cache.append((stat, current_time))
        # remove all entries from the cache that are older than 1 second
        self.cache = [(x, t) for x, t in self.cache if current_time - t <= 1]

        # return the difference between the last and first entry of the cache
        # this is equal to the bytes read since the last second
        return float(self.cache[-1][0] - self.cache[0][0]) / 1000**2

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        # the maximum is not known beforehand, so make it adaptive
        return None


class CPUTempStat(Stat):
    """
    tag: ``core.cpu_temp``

    settings: none

    Tracks the CPU temperature of the user.
    """
    name = 'CPU Temperature [°C]'
    base_tag = 'cpu_temp'

    @classmethod
    def check_availability(cls):
        try:
            temps = psutil.sensors_temperatures()
        except AttributeError:
            raise exceptions.StatNotAvailableError(
                'psutil.sensors_temperatures is not available on your system.')
        # psutil.sensors_temperatures returns a dictionary
        # consisting of multiple temperature measurements
        # `coretemp` is the only one currently considered
        # the stat is not available if it does not exist in the dictionary
        if 'coretemp' not in temps:
            raise exceptions.StatNotAvailableError(
                'CPU temperature sensor could not be found.')

    def __init__(self, fps):
        critical_temps = [x.critical for x in self.get_core_temps()]
        # set the maximum to the average critical temperature of all cores
        # in the tests so far, the critical temperature of all cores has
        # always been the same
        self._maximum = sum(critical_temps) / len(critical_temps)
        super(CPUTempStat, self).__init__(fps=fps)

    def get_core_temps(self):
        # get the coretemp measurements
        return psutil.sensors_temperatures()['coretemp']

    def get_stat(self):
        # get the temperature of all coress
        core_temps = [x.current for x in self.get_core_temps()]
        # return the temperature average of all cores
        return sum(core_temps) / len(core_temps)

    @property
    def minimum(self):
        return None

    @property
    def maximum(self):
        return self._maximum


class ProcessTracker():
    """
    Singleton wrapper for tracking process information like cpu and
    RAM usage of each process. Needed by core.ram_usage and core.cpu_usage
    for their contributor breakdown.
    """
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
        """Class actually tracking the processes."""
        def __init__(self):
            self._stop = False
            self._stopped = False
            self.processes = {}

            # start a thread for continuously reading all processes
            self._thread = threading.Thread(target=self._read_processes)
            self._thread.start()

        def _read_processes(self):
            # while the tracker is running, read the cpu and ram usage
            # of all running processes
            while not self._stop:
                iterator = psutil.process_iter()
                _processes = {}

                for proc in iterator:
                    name = re.split(r'[\W\s]+', proc.name())[0]
                    try:
                        proc_cpu_usage = proc.cpu_percent()
                        proc_memory = proc.memory_info().vms
                    except psutil._exceptions.AccessDenied:
                        # an AccessDenied error might occur if permon is not
                        # allowed to view the stats of distinct processes
                        # in that case, stop the process tracker thread
                        break

                    if name not in _processes:
                            _processes[name] = {
                                'cpu': proc_cpu_usage,
                                'ram': proc_memory
                            }
                    else:
                        _processes[name]['cpu'] += proc_cpu_usage
                        _processes[name]['ram'] += proc_memory

                    # sleep for a short time to allow the UI thread to continue
                    if self._stop:
                        break
                    time.sleep(0.02)

                self.processes = _processes

            self._stopped = True

        def get_contributors(self, tag, n=5, adapt_to=None):
            """
            Get the top n contributors to a tag
            where `tag` is either `cpu` or `ram`.
            If adapt_to is not None, scale the contributors such that
            their sum is equal to adapt_to.
            """
            if not self.processes:
                return []

            processes = self.processes.items()
            contributors = sorted(processes, key=lambda proc: proc[1][tag],
                                  reverse=True)
            contributors = [[key, value[tag]] for key, value in contributors
                            if value[tag] != 0]
            # if there are contributors but all of them are zero
            # return early too
            if len(contributors) == 0:
                return []

            if adapt_to is not None:
                value_sum = max(sum(x[1] for x in contributors), 1e-6)
                # scale the contributors so that they amount to adapt_to
                for i, (_, value) in enumerate(contributors):
                    contributors[i][1] = value / value_sum * adapt_to
                # combine the contributors that are smaller than the top n
                # into one
                remainder = adapt_to - sum(x[1] for x in contributors[:n-1])
                contributors.insert(0, ['other', remainder])

            return contributors[:n]

    def delete_instance(self):
        self.instance._stop = True
        while not self._stopped:
            continue

        self.instance = None
