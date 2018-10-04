import os
from abc import ABC, abstractmethod
import importlib
import inspect
from permon import exceptions


class Stat(ABC):
    windows_classes = []
    linux_classes = []

    def __init__(self, n_top=5):
        if not self.is_available():
            raise exceptions.InvalidStatError(
                'Unavailable stats can not be instantiated.')
        self.has_top_info = isinstance(self.get_stat(), tuple)
        self.n_top = n_top

    @classmethod
    def is_available(cls):
        return True

    @classmethod
    def get_full_tag(cls):
        full_path = inspect.getfile(cls)
        base = os.path.splitext(os.path.basename(full_path))[0]
        return f'{base}.{cls.tag}'

    @classmethod
    def _validate_stat(cls, check_cls):
        if not hasattr(check_cls, 'name'):
            raise exceptions.InvalidStatError(
                'Stats must have a static name attribute.')
        if not hasattr(check_cls, 'tag'):
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

    return stats
