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

.. autoclass:: permon.backend.stats.core.CPUStat()
.. autoclass:: permon.backend.stats.core.RAMStat()
.. autoclass:: permon.backend.stats.core.ReadStat()
.. autoclass:: permon.backend.stats.core.WriteStat()
.. autoclass:: permon.backend.stats.core.CPUTempStat()
.. autoclass:: permon.backend.stats.core.JupyterRAMUsage()

Extending permon with custom stats
----------------------------------