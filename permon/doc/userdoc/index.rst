User documentation
==================


What is permon?
---------------

Permon is a tool to display live line charts in a clear, uncluttered way. Permon comes prepackaged
with a lot of useful stats for monitoring the performance of your PC. It is developed with a focus
on only showing you things you care about, not everything you can monitor in your system.

Permon is developed in Python 3. There is a good chance you already have Python on your system. If
not, install it (recommended: `Miniconda <https://conda.io/miniconda.html/>`_. Run ``pip
install permon`` in your preferred command line to install permon. Permon can then be started from the command line.

Synopsis
""""""""

.. argparse::
   :module: permon
   :func: get_parser
   :prog: permon
   :nodescription:

Stats
-----

Permon comes prepackaged with some useful stats to monitor the performance of your PC. You can also add custom stats to Permon.
See `Extending permon with custom stats`_ to see how to do that. The following stats are always part of Permon:

.. autoclass:: permon.backend.stats.core.CPUStat()
.. autoclass:: permon.backend.stats.core.RAMStat()
.. autoclass:: permon.backend.stats.core.GPUStat()
.. autoclass:: permon.backend.stats.core.ReadStat()
.. autoclass:: permon.backend.stats.core.WriteStat()
.. autoclass:: permon.backend.stats.core.CPUTempStat()
.. autoclass:: permon.backend.stats.jupyter.JupyterRAMUsage()

Extending permon with custom stats
----------------------------------

Permon can be extended by adding custom stats. Custom stats have to be put in the ``stats`` subdirectory of the user
config directory. You can find your user config directory by executing ``permon config show`` and looking for *Config directory*.

.. hint::
    On Linux, execute ``cd `permon config show | grep -o "\S*/permon$"``` to directly change your directory to permon's config directory.

In the config directory, make a subdirectory ``stats`` and create a file called ``<name>.permon.py`` in the subdirectory where ``<name>`` is the name for
your suite of stats e. g. ``custom.permon.py``.

The tag of your stat will then be ``<name>.<base_tag>`` where ``<base_tag>`` is the static ``base_tag`` attribute
of your stat class.

You can now start creating stats in this file. They will automatically be discovered by permon. A simple custom stat could look like this:

.. code-block:: python

    import math
    from permon.backend import Stat


    class SineStat(Stat):
        name = 'Sine'
        base_tag = 'sine'

        def __init__(self, fps):
            self.t = 0
            super(SineStat, self).__init__(fps)

        def get_stat(self):
            self.t += 1 / self.fps
            return math.sin(self.t)

        @property
        def maximum(self):
            return 1

        @property
        def minimum(self):
            return -1

All stats must inherit from the ``permon.backend.Stat`` base class.

Adding settings to a stat
"""""""""""""""""""""""""

Stats can have settings to conventienly change some aspects of the stat. Extending the example from above:

.. code-block:: python

    import math
    from permon.backend import Stat


    class SineStat(Stat):
        name = 'Sine'
        base_tag = 'sine'
        default_settings = {
            'speed': 1.
        }

        def __init__(self, fps):
            self.t = 0
            super(SineStat, self).__init__(fps)

        def get_stat(self):
            self.t += 1 / self.fps * self.settings['speed']
            return math.sin(self.t)

        @property
        def maximum(self):
            return 1

        @property
        def minimum(self):
            return -1

Note that ``default_settings`` only stores the default settings. In the calculation, ``self.settings`` is used because it stores the settings that
are entered in the UI.

Every setting must have a default value. Every value should be a basic python data type (string, float, integer, ...) because
permon will automatically cast the user-entered string to the type specified in the ``default_settings``.

If you need more advanced data types like JSON, make the default value a string and manually convert it to the needed data type afterwards.

Making a stat conditionally available
"""""""""""""""""""""""""""""""""""""

Some stats are not always available, like :meth:`permon.backend.stats.JupyterRAMUsage` which needs ``nvidia-smi`` installed.

To add some logic to check whether your stat is available or not, implement the :meth:`Stat.check_availability` method.
This method must raise a :meth:`permon.exceptions.StatNotAvailableError` if the stat is not available. ``cls.settings`` can also be used
in :meth:`Stat.check_availability` to e. g. disallow some settings. Further expanding the example from above:

.. code-block:: python

    import math
    from permon.backend import Stat
    from permon import exceptions


    class SineStat(Stat):
        name = 'Sine'
        base_tag = 'sine'
        default_settings = {
            'speed': 1.
        }

        @classmethod
        def check_availability(cls):
            if cls.settings['speed'] <= 0:
                raise exceptions.StatNotAvailableError(
                    'Speed must be greater than zero.')

        def __init__(self, fps):
            self.t = 0
            super(SineStat, self).__init__(fps)

        def get_stat(self):
            self.t += 1 / self.fps * self.settings['speed']
            return math.sin(self.t)

        @property
        def maximum(self):
            return 1

        @property
        def minimum(self):
            return -1

That already covers the full functionality of any stat.
To see how the prepackaged stats are implemented, see the `source on github <https://github.com/bminixhofer/permon/blob/dev/permon/backend/stats/core.py>`_.