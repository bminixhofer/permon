import psutil
import threading
from subprocess import Popen, PIPE
from permon.classes import Stat
import os


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


class IoReader():
    instance = None
    n_instances = 0

    class __IoReader:
        def __init__(self):
            self._read = 0
            self._write = 0
            self._thread = threading.Thread(target=self._io_process)
            self._thread.start()

            self._thread_is_stopped = False
            self._stop_thread = False

        def _io_process(self):
            p = Popen('iostat -m 1 -g ALL -H'.split(),
                      stdout=PIPE, stderr=PIPE)
            for line in p.stdout:
                line = line.decode('utf-8')
                if line.strip().startswith('ALL'):
                    stat_str = line.split()[2:4]
                    # replace , with . to be convert the string to a number
                    read_write = [float(x.replace(',', '.')) for x in stat_str]
                    self._read = read_write[0]
                    self._write = read_write[1]

                if self._stop_thread:
                    self._thread_is_stopped = True
                    break

        def stop_thread(self):
            self._stop_thread = True
            while not self._thread_is_stopped:
                continue

        @property
        def read(self):
            return self._read

        @property
        def write(self):
            return self._write

    def __del__(self):
        IoReader.n_instances -= 1
        # delete the instance when the last singleton wrapper is deleted
        if IoReader.n_instances == 0:
            IoReader.instance.stop_thread()
            IoReader.instance = None

    def __init__(self):
        IoReader.n_instances += 1
        if not self.instance:
            IoReader.instance = self.__IoReader()

    def __getattr__(self, name):
        return getattr(self.instance, name)


@Stat.linux
class ReadStat(Stat):
    name = 'Disk Read Speed in MiB / s'
    tag = 'read_speed'

    def __init__(self):
        self.reader = IoReader()

    def get_stat(self):
        return self.reader.read

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return None

    def destruct(self):
        del self.reader


@Stat.linux
class WriteStat(Stat):
    name = 'Disk Write Speed in MiB / s'
    tag = 'write_speed'

    def __init__(self):
        self.reader = IoReader()

    def get_stat(self):
        return self.reader.write

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return None


def get_available_stats():
    if os.name == 'posix':
        return Stat.linux_classes
    elif os.name == 'nt':
        return Stat.windows_classes
