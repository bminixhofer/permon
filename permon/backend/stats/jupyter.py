import os
import sys
import csv
import json
import glob
import appdirs
import warnings
from jupyter_client import BlockingKernelClient
from permon.backend import Stat


@Stat.windows
@Stat.linux
class JupyterRAMUsage(Stat):
    name = 'RAM Usage of objects in a Python Jupyter Notebook [MB]'
    base_tag = 'ram_usage'

    @classmethod
    def _read_latest_connection_file(cls):
        """
        Reads the latest jupyter kernel connection file.
        https://jupyter.readthedocs.io/en/latest/projects/jupyter-directories.html.
        """
        try:
            runtime_dir = os.path.join(os.environ['XDG_RUNTIME_DIR'],
                                       'jupyter')
        except KeyError:
            runtime_dir = os.path.join(sys.prefix,
                                       'share',
                                       'jupyter',
                                       'runtime')
        files = glob.glob(os.path.join(runtime_dir, 'kernel-*.json'))
        if len(files) == 0:
            return None

        # use the latest connection file
        connection_file = max(files, key=os.path.getctime)
        with open(connection_file, 'r') as f:
            return json.load(f)

    @classmethod
    def is_available(cls):
        if cls._read_latest_connection_file() is None:
            warnings.warn('Could not find any running kernel.')
            return False

        return True

    def __init__(self, fps):
        self.config = self._read_latest_connection_file()
        data_dir = appdirs.user_data_dir('permon', 'bminixhofer')
        os.makedirs(data_dir, exist_ok=True)

        self.usage_file = os.path.join(data_dir, 'jupyter_ram_usage.csv')
        open(self.usage_file, 'w').close()

        self.setup_code = f"""
if '_permon_running' not in globals() or not _permon_running:
    import threading
    import csv
    import sys
    import time
    from pympler import asizeof
    from types import ModuleType

    def _permon_get_ram_usage_per_object():
        while _permon_running:
            ram_usage = []
            global_vars = [key for key in globals() if not key.startswith('_')]
            for name in global_vars:
                value = globals()[name] if name in globals() else None
                if isinstance(value, ModuleType):
                    continue

                try:
                    ram_usage.append((name, asizeof.asizeof(value)))
                except TypeError:
                    continue

            with open('{self.usage_file}', 'w') as f:
                writer = csv.writer(f, delimiter=',')
                for name, ram in ram_usage:
                    writer.writerow([name, ram])
            time.sleep(10)

    _permon_thread = threading.Thread(target=_permon_get_ram_usage_per_object)
    _permon_running = True
    _permon_thread.start()
"""
        self.teardown_code = """
_permon_running = False
"""
        self.client = BlockingKernelClient()
        self.client.load_connection_info(self.config)
        self.client.start_channels()
        self.client.execute(self.setup_code)
        super(JupyterRAMUsage, self).__init__(fps=fps)

    def __del__(self):
        self.client.execute(self.teardown_code)
        self.client.stop_channels()

    def get_stat(self):
        ram_usage = []
        with open(self.usage_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                ram_usage.append(
                    (row[0], float(row[1]) / 1000**2)
                )
        ram_usage = sorted(ram_usage, key=lambda x: x[1], reverse=True)

        return sum(x[1] for x in ram_usage), ram_usage[:5]

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return None
