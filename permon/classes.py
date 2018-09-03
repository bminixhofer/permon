from abc import ABC, abstractmethod
import numpy as np


class Stat(ABC):
    windows_classes = []
    linux_classes = []

    @classmethod
    def _validate_stat(cls, check_cls):
        assert hasattr(check_cls, 'name'), \
            'Stats must have a static name attribute.'
        assert hasattr(check_cls, 'tag'), \
            'Stats must have a static tag attribute.'

    @classmethod
    def windows(cls, check_cls):
        Stat._validate_stat(check_cls)
        Stat.windows_classes.append(check_cls)
        return check_cls

    @classmethod
    def linux(cls, check_cls):
        Stat._validate_stat(check_cls)
        Stat.linux_classes.append(check_cls)
        return check_cls

    @abstractmethod
    def get_stat(self):
        pass

    @property
    @abstractmethod
    def minimum(self):
        pass

    @property
    @abstractmethod
    def maximum(self):
        pass

    def destruct(self):
        pass


class Monitor(ABC):
    def __init__(self, stat_func, title, buffer_size, fps, color,
                 minimum=None, maximum=None):
        if minimum and maximum:
            assert np.abs(maximum - minimum) > 0, \
                'Graph range must be greater than zero.'

        self.stat_func = stat_func
        self.title = title
        self.buffer_size = buffer_size
        self.fps = fps
        self.color = color
        self.minimum = minimum
        self.maximum = maximum

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def paint(self):
        pass


class MonitorApp(ABC):
    def __init__(self, stat_funcs, colors, buffer_size, fps):
        self.stat_funcs = stat_funcs
        self.colors = colors
        self.buffer_size = buffer_size
        self.fps = fps
        self.monitors = []

    @abstractmethod
    def initialize(self):
        pass

    def update(self):
        for monitor in self.monitors:
            monitor.update()

    @abstractmethod
    def paint(self):
        pass
