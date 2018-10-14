import os
from abc import ABC, abstractmethod
import importlib
import inspect
from permon import exceptions


class Stat(ABC):
    windows_classes = []
    linux_classes = []
    _initialized = False

    def __init__(self, n_contributors=5):
        if not self._initialized:
            raise exceptions.InvalidStatError(
                'The stat class is not initialized.')

        if not self.is_available():
            raise exceptions.InvalidStatError(
                'Unavailable stats can not be instantiated.')
        self.has_contributor_breakdown = isinstance(self.get_stat(), tuple)
        self.n_contributors = n_contributors

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def _init_tags(cls):
        if not cls._initialized:
            full_path = inspect.getfile(cls)
            filename = os.path.splitext(os.path.basename(full_path))[0]

            # define tag and root_tag
            # base_tag has already been defined by the stat creator
            cls.root_tag = filename
            cls.tag = f'{cls.root_tag}.{cls.base_tag}'

            cls._initialized = True

    @classmethod
    def _validate_stat(cls, check_cls):
        if not hasattr(check_cls, 'name'):
            raise exceptions.InvalidStatError(
                'Stats must have a static name attribute.')
        if not hasattr(check_cls, 'base_tag'):
            raise exceptions.InvalidStatError(
                'Stats must have a static tag attribute.')

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


def _import_all_stats():
    file_dir = os.path.dirname(os.path.realpath(__file__))
    stat_files = os.listdir(os.path.join(file_dir, 'stats'))
    for f in stat_files:
        base, ext = os.path.splitext(f)
        if ext == '.py':
            importlib.import_module(f'permon.backend.stats.{base}')


def get_all_stats():
    _import_all_stats()

    if os.name == 'posix':
        stats = Stat.linux_classes
    elif os.name == 'nt':
        stats = Stat.windows_classes
    for stat in stats:
        stat._init_tags()

    stats = sorted(stats, key=lambda stat: stat.tag)
    return stats


def get_stats_from_tags(tags):
    is_one = False
    if not isinstance(tags, list):
        is_one = True
        tags = [tags]

    verify_tags(tags)

    stats = []
    for stat in get_all_stats():
        if stat.tag in tags and stat.is_available():
            stats.append(stat)

    return stats[0] if is_one else stats


def verify_tags(tags):
    if not isinstance(tags, list):
        tags = [tags]

    all_tags = [stat.tag for stat in get_all_stats()]

    for tag in tags:
        if tag not in all_tags:
            raise exceptions.InvalidStatError(f'stat "{tag}" does not exist.')
