import sys
import io
import signal
import numpy as np
import blessings
import pytest
from permon.frontend import terminal
np.random.seed(0)


def abort_after_seconds(timeout, *args):
    def decorate(f):
        def new_f(*args):
            signal.signal(signal.SIGALRM, lambda: None)
            signal.alarm(timeout)
            return f(*args)
            signal.alarm(0)

        new_f.__name__ = f.__name__
        return new_f
    return decorate


def capture_out(func):
    f = io.StringIO()
    prev_stdout = sys.stdout

    sys.stdout = f
    func()
    sys.stdout = prev_stdout

    return f.getvalue()


class TestTerminal(object):
    def test_resolution(self):
        resolution = (10, 20)
        minimum = 0
        maximum = 100

        def stat_func():
            return np.random.randint(minimum, maximum)

        monitor = terminal.TerminalMonitor(stat_func, title='Test Monitor',
                                           buffer_size=100, fps=10,
                                           color=lambda x: x,
                                           resolution=resolution,
                                           minimum=0, maximum=100)
        # fill the chart with arbitrary measurements
        for _ in range(resolution[1]):
            monitor.update()

        out = capture_out(monitor.paint)
        rows = out.split('\n')[:-1]

        assert len(rows) == resolution[0]

        row_lengths = [len(x) for x in rows[1:]]
        assert row_lengths.count(resolution[1]) == len(row_lengths)

    def test_update(self):
        minimum = 0
        maximum = 100

        def stat_func():
            return 50

        monitor = terminal.TerminalMonitor(stat_func, title='Test Monitor',
                                           buffer_size=100, fps=10,
                                           color=lambda x: x,
                                           resolution=(10, 20),
                                           minimum=minimum,
                                           maximum=maximum)

        assert (monitor.values == minimum).all()

        monitor.update()
        assert (monitor.values[:-1] == minimum).all()
        assert monitor.values[-1] == stat_func()

    def test_init_app(self, capsys):
        class MockTerminal(blessings.Terminal):
            def __init__(self):
                super(MockTerminal, self).__init__(self, force_styling=None)

            @property
            def height(self):
                return 20

            @property
            def width(self):
                return 20

            @property
            def is_a_tty(self):
                return True

        stat_funcs = [(lambda: 0, {
            'title': 'Test Function',
            'minimum': 0,
            'maximum': 100
        })]

        app = terminal.TerminalApp(stat_funcs, colors=[],
                                   buffer_size=500, fps=10)
        app.term = MockTerminal()

        init = abort_after_seconds(4)(app.initialize)
        with pytest.raises(SystemExit) as exit_info:
            init()
        assert exit_info.value.code == 0
