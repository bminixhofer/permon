import os
import csv
import json
import glob
import appdirs
from jupyter_core.paths import jupyter_runtime_dir
from jupyter_client import BlockingKernelClient
from permon.backend import Stat
from permon import exceptions


class JupyterRAMUsage(Stat):
    """
    tag: ``jupyter.ram_usage``

    settings:

    .. code-block:: javascript

        {
            "connection info": "",
            "query interval [s]": 1
        }

    Tracks the RAM usage of all variables in
    a user-specified jupyter notebook. If no connection info is given in the
    settings, take the kernel with the latest start date.

    ``connection info`` must be a string containing the info displayed when
    running ``%connect_info`` in a jupyter notebook
    (you can directly copy-paste it).

    ``query interval [s]`` specifies how often the thread running in the
    jupyter notebook should read the variables. The lower this is, the higher
    the resolution of the stat but it might start affecting the speed of
    your notebook when too low.

    Note that RAM tracked in this way is not equal to the actual RAM
    the OS needs because some further optimization is done by e. g. numpy
    to reduce the OS memory usage.
    """
    name = 'RAM Usage of objects in a Python Jupyter Notebook [MB]'
    base_tag = 'ram_usage'
    default_settings = {
        'connection info': '',
        # how often the memory usage is read in the jupyter notebook
        'query interval [s]': 1.
    }

    @classmethod
    def _read_latest_connection_file(cls):
        """
        Reads the latest jupyter kernel connection file.
        https://jupyter.readthedocs.io/en/latest/projects/jupyter-directories.html.
        """
        runtime_dir = jupyter_runtime_dir()
        files = glob.glob(os.path.join(runtime_dir, 'kernel-*.json'))
        if len(files) == 0:
            return None

        # use the latest connection file
        connection_file = max(files, key=os.path.getctime)
        with open(connection_file, 'r') as f:
            return json.load(f)

    @classmethod
    def get_connection_info(cls):
        """
        Get the target kernel connection info.
        Returns a dictionary of the connection info supplied
        in the settings, or the latest started kernel if none is given.
        Retuns `None` if no kernel has been found.
        """
        if len(cls.settings['connection info']) == 0:
            return cls._read_latest_connection_file()
        return json.loads(cls.settings['connection info'])

    @classmethod
    def check_availability(cls):
        # the stat is not available if no suitable connection info
        # can be found
        if cls.get_connection_info() is None:
            raise exceptions.StatNotAvailableError(
                'Could not find any running kernel.')

    def __init__(self, fps):
        self.config = self.get_connection_info()
        data_dir = appdirs.user_data_dir('permon', 'bminixhofer')
        os.makedirs(data_dir, exist_ok=True)

        self.usage_file = os.path.join(data_dir, 'jupyter_ram_usage.csv')
        open(self.usage_file, 'w').close()

        # self.setup_code is the code that is run in the notebook when the
        # stat is instantiated. It starts a thread which reads the memory
        # usage of all public variables in a set interval and saves it to a
        # csv file in the user data directory
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
            time.sleep({self.settings['query interval [s]']})

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
        # stop the thread running in the jupyter notebook
        # and stop the connection to the kernel upon deletion
        self.client.execute(self.teardown_code)
        self.client.stop_channels()

    def get_stat(self):
        # reads the csv file the setup code has written to
        ram_usage = []
        with open(self.usage_file, 'r') as f:
            reader = csv.reader(f)
            for row in reader:
                ram_usage.append(
                    (row[0], float(row[1]) / 1000**2)
                )
        # sort the ram_usage list so that the largest variables come first
        ram_usage = sorted(ram_usage, key=lambda x: x[1], reverse=True)

        # return the sum of RAM usage and the variables taking up the most RAM
        return sum(x[1] for x in ram_usage), ram_usage[:5]

    @property
    def minimum(self):
        return 0

    @property
    def maximum(self):
        return None
