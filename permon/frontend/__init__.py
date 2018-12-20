import os
import sys
from abc import ABC, abstractmethod
from collections import OrderedDict
from importlib import util
import logging
from permon import exceptions, backend, config
import subprocess


class Monitor(ABC):
    """
    Base class for all monitors.
    A monitor wraps a stat by adding a way to display it.
    """
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
        """
        Update the monitor by i. e. fetching the latest value from its stat.
        """
        pass


class MonitorApp(ABC):
    """
    Base class for all monitor apps.
    A monitor app consists of one or more `Monitor` instances to display stats.
    """
    @classmethod
    def get_asset_path(cls, *relative_path):
        """Get an asset from the shared asset directory for all frontends."""
        directory_path = os.path.dirname(__file__)
        absolute_path = os.path.join(directory_path, 'assets', *relative_path)
        return absolute_path

    @classmethod
    def verify_installed(cls, package_name):
        """
        Verify the package with `package_name` is installed.
        If it is not installed, prompt the user to install it.
        """
        spec = util.find_spec(package_name)
        if spec is None or spec.loader is None:
            choice = input(f'Required package "{package_name}" is '
                           'not installed. Install? (y)es / (n)o: ')

            if choice.lower() in ['y', 'yes']:
                pipargs = ['pip', 'install', package_name]
                command_str = ' '.join(pipargs)

                return_code = subprocess.call(pipargs)
                if return_code != 0:
                    logging.error(f'"{command_str}" failed. '
                                  f'Please install {package_name} manually.')
                    sys.exit(return_code)
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
        """Get all stat classes that could be displayed in the frontend."""
        return backend.get_all_stats()

    def get_displayed_stats(self):
        """Get all stat classes that are currently displayed."""
        return [type(monitor.stat) for monitor in self.monitors]

    def get_not_displayed_stats(self):
        """
        Get all stat classes that are currently not displayed
        but could be tried to display.
        """
        stats = set(self.get_all_stats()) - set(self.get_displayed_stats())
        return sorted(list(stats), key=lambda stat: stat.tag)

    def next_color(self):
        """
        Get the least used color of displayed monitors to determine
        which color the next monitor should have.
        """
        color_counts = OrderedDict([(color, 0) for color in self.colors])
        for monitor in self.monitors:
            color_counts[monitor.color] += 1

        min_count = min(color_counts.values())
        # return the first color with the least amount of usages
        for color, count in color_counts.items():
            if count == min_count:
                return color

    @abstractmethod
    def initialize(self):
        pass

    def add_stat(self, stat, add_to_config=True):
        """
        Adds `stat` to the displayed stats and if `add_to_config`
        is true to the user configuration.
        """
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
        """
        Removes `stat` from the displayed stats and if `remove_from_config`
        is true from the user configuration.
        """
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
        """
        Try to make the frontend available by i. e. prompting the user to
        install required modules.
        """
        pass

    def update(self):
        """Update the app by updating every monitor."""
        for monitor in self.monitors:
            monitor.update()

    @property
    def stats(self):
        """Get all stat instances from the currently displayed monitors."""
        return [monitor.stat for monitor in self.monitors]
