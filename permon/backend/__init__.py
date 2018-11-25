import os
from abc import ABC, abstractmethod
import glob
import runpy
from permon import exceptions, config

_imported_stats = False


class Stat(ABC):
    _initialized = False
    windows_classes = []
    linux_classes = []
    default_settings = {}

    def __init__(self, fps):
        if not self._initialized:
            raise exceptions.InvalidStatError(
                'The stat class is not initialized.')

        try:
            self.check_availability()
        except exceptions.StatNotAvailableError:
            raise exceptions.InvalidStatError(
                'Unavailable stats can not be instantiated.')
        self.fps = fps
        self.has_contributor_breakdown = isinstance(self.get_stat(), tuple)

    @classmethod
    def _init_tags(cls):
        if not cls._initialized:
            base = os.path.basename(cls.__module__)
            root_tag = base[:base.index('.permon.py')]
            # define tag and root_tag
            # base_tag has already been defined by the stat creator
            cls.root_tag = root_tag
            cls.tag = f'{cls.root_tag}.{cls.base_tag}'
            cls.settings = cls.default_settings.copy()

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
    def set_settings(cls, settings):
        assert set(settings.keys()).issubset(set(cls.default_settings.keys()))

        for key, value in settings.items():
            key_type = type(cls.default_settings[key])
            # cast the settings value to the type
            # specified in the default settings
            cls.settings[key] = key_type(value)

    @classmethod
    def check_availability(cls):
        pass

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
    here = os.path.dirname(os.path.realpath(__file__))
    default_stat_dir = os.path.join(here, 'stats', '*.permon.py')
    custom_stat_dir = os.path.join(config.config_dir, 'stats', '*.permon.py')

    default_stat_files = glob.glob(default_stat_dir)
    custom_stat_files = glob.glob(custom_stat_dir)

    dup = set(os.path.basename(x) for x in default_stat_files).intersection(
          set(os.path.basename(x) for x in custom_stat_files))
    assert len(dup) == 0, \
        ('Custom stat files must not have the same name as default ones. '
         f'{dup} collides.')

    for path in default_stat_files + custom_stat_files:
        runpy.run_path(path, run_name=path)


def get_all_stats():
    global _imported_stats

    if not _imported_stats:
        _import_all_stats()
        _imported_stats = True

    if os.name == 'posix':
        stats = Stat.linux_classes
    elif os.name == 'nt':
        stats = Stat.windows_classes
    for stat in stats:
        stat._init_tags()

    stats = sorted(stats, key=lambda stat: stat.tag)
    return stats


def get_stats_from_repr(stat_repr):
    is_one = False
    if not isinstance(stat_repr, list):
        is_one = True
        stat_repr = [stat_repr]

    stat_dicts = config.parse_stats(stat_repr)
    tags = [x['tag'] for x in stat_dicts]
    verify_tags(tags)

    stats = []
    for stat in get_all_stats():
        try:
            index = tags.index(stat.tag)
            stat.check_availability()
            stat.set_settings(stat_dicts[index]['settings'])

            stats.append(stat)
        except ValueError:
            continue

    return stats[0] if is_one else stats


def verify_tags(tags):
    if not isinstance(tags, list):
        tags = [tags]

    all_tags = [stat.tag for stat in get_all_stats()]

    for tag in tags:
        if tag not in all_tags:
            raise exceptions.InvalidStatError(f'stat "{tag}" does not exist.')
