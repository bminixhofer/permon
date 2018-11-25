import os
from abc import ABC, abstractmethod
from collections import OrderedDict
from importlib import util
import logging
from permon import exceptions, backend, config

# support pip 9 and pip >= 10
try:
    from pip import main as pipmain
except ImportError:
    from pip._internal import main as pipmain


class Monitor(ABC):
    def __init__(self, stat, buffer_size, fps, color, app):
        # the only place a stat is ever instantiated
        self.stat = stat(fps=fps)

        if self.stat.minimum is not None and self.stat.maximum is not None:
            assert abs(self.stat.maximum - self.stat.minimum) > 0, \
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


class MonitorApp(ABC):
    @classmethod
    def get_asset_path(cls, *relative_path):
        directory_path = os.path.dirname(__file__)
        absolute_path = os.path.join(directory_path, 'assets', *relative_path)
        return absolute_path

    @classmethod
    def verify_installed(cls, package_name):
        spec = util.find_spec(package_name)
        if spec is None or spec.loader is None:
            choice = input(f'Required package "{package_name}" is '
                           'not installed. Install? (y)es / (n)o: ')

            if choice.lower() in ['y', 'yes']:
                pipmain(['install', package_name])
            else:
                raise exceptions.FrontendNotAvailableError(
                    f'{package_name} is not installed.')

    def __init__(self, stats, colors, buffer_size, fps):
        assert len(colors) > 0, 'App must have at least one color.'

        self.initial_stats = stats
        self.colors = colors
        self._color_index = 0
        self.buffer_size = buffer_size
        self.fps = fps
        self.monitors = []

        if len(self.initial_stats) == 0:
            raise exceptions.NoStatError()

    def get_all_stats(self):
        return backend.get_all_stats()

    def get_displayed_stats(self):
        return [type(monitor.stat) for monitor in self.monitors]

    def get_not_displayed_stats(self):
        stats = set(self.get_all_stats()) - set(self.get_displayed_stats())
        return sorted(list(stats), key=lambda stat: stat.tag)

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

    def add_stat(self, stat, add_to_config=True):
        if add_to_config:
            stats = config.get_config()['stats'].copy()
            tags = [x['tag'] for x in config.parse_stats(stats)]

            if stat.tag not in tags:
                if stat.settings == stat.default_settings:
                    stats.append(stat.tag)
                else:
                    stats.append({
                        'tag': stat.tag,
                        'settings': stat.settings
                    })
            config.set_config({
                'stats': stats
            })
        logging.info(f'Added stat {stat.tag}')

    def remove_stat(self, stat, remove_from_config=True):
        if remove_from_config:
            stats = config.get_config()['stats'].copy()
            tags = [x['tag'] for x in config.parse_stats(stats)]
            try:
                index = tags.index(stat.tag)
                del stats[index]
            except ValueError:
                logging.error((f'Removing stat {stat.tag} failed. '
                               'Stat might already have been removed.'
                               ))
            config.set_config({
                'stats': stats
            })
        logging.info(f'Removed stat {stat.tag}')

    def make_available(self):
        pass

    def update(self):
        for monitor in self.monitors:
            monitor.update()

    @property
    def stats(self):
        return [monitor.stat for monitor in self.monitors]
