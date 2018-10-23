import os
from abc import ABC, abstractmethod
from collections import OrderedDict
import numpy as np
from permon import exceptions


class Monitor(ABC):
    def __init__(self, stat, buffer_size, fps, color, app):
        # the only place a stat is ever instantiated
        self.stat = stat(fps=fps)

        if self.stat.minimum is not None and self.stat.maximum is not None:
            assert np.abs(self.stat.maximum - self.stat.minimum) > 0, \
                'Graph range must be greater than zero.'

        self.buffer_size = buffer_size
        self.fps = fps
        self.color = color
        self.app = app

    def remove(self):
        self.app.remove_monitor(self)

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def paint(self):
        pass


class MonitorApp(ABC):
    @classmethod
    def get_asset_path(cls, *relative_path):
        directory_path = os.path.dirname(__file__)
        absolute_path = os.path.join(directory_path, 'assets', *relative_path)
        return absolute_path

    def __init__(self, stats, colors, buffer_size, fps):
        assert len(colors) > 0, 'App must have at least one color.'

        self.stats = stats
        self.colors = colors
        self._color_index = 0
        self.buffer_size = buffer_size
        self.fps = fps
        self.monitors = []

        if len(self.stats) == 0:
            raise exceptions.NoStatError()

    def next_color(self):
        color_counts = OrderedDict([(color, 0) for color in self.colors])
        for monitor in self.monitors:
            color_counts[monitor.color] += 1

        min_count = min(color_counts.values())
        for color, count in color_counts.items():
            if count == min_count:
                return color

    @abstractmethod
    def initialize(self):
        pass

    def update(self):
        for monitor in self.monitors:
            monitor.update()

    @abstractmethod
    def paint(self):
        pass
