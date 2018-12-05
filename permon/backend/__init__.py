import os
from abc import ABC, ABCMeta, abstractmethod
import glob
import runpy
from permon import exceptions, config


class MetaStat(ABCMeta):
    """Stat metaclass. Used to keep track of all descendants of Stat."""
    stat_classes = []

    def __new__(cls, *args, **kwargs):
        new_class = super().__new__(cls, *args, **kwargs)
        # register the class as stat if it does not immediately inherit ABC
        if ABC not in new_class.__bases__:
            new_class._init_tags()
            cls.stat_classes.append(new_class)
        return new_class


class Stat(ABC, metaclass=MetaStat):
    """
    Base class for all stats.
    Stats are only ever instantiated when they are really displayed.
    Most of the time the class itself is used to represent a stat.
    """
    _initialized = False
    default_settings = {}

    def __init__(self, fps):
        """
        Construct a stat.
        self.get_stat must already work when this is called.
        """
        if not self._initialized:
            raise exceptions.InvalidStatError(
                'The stat class is not initialized.')

        try:
            self.check_availability()
        except exceptions.StatNotAvailableError:
            raise exceptions.InvalidStatError(
                'Unavailable stats can not be instantiated.')
        self.fps = fps
        # check if the class returns a tuple. in that case, it contains a
        # breakdown of contributors to the stat
        self.has_contributor_breakdown = isinstance(self.get_stat(), tuple)

    @classmethod
    def _init_tags(cls):
        """
        Initialise the tags of the stat class.
        Must be called before anything else is done with the stat class.
        """
        cls._validate_stat()
        if not cls._initialized:
            base = os.path.basename(cls.__module__)
            index = None
            if not base.endswith('.py'):
                # module was imported regularly, not via runpy
                root_tag = base.split('.')[-1]
            else:
                try:
                    # check whether it is a user-defined stat
                    # which must end with .permon.py
                    index = base.index('.permon.py')
                except ValueError:
                    # otherwise, it is a prepackaged stat
                    # which just ends with .py
                    index = base.index('.py')
            root_tag = base[:index]
            # define tag and root_tag
            # base_tag has already been defined by the stat creator
            cls.root_tag = root_tag
            cls.tag = f'{cls.root_tag}.{cls.base_tag}'
            cls.settings = cls.default_settings.copy()

            cls._initialized = True

    @classmethod
    def _validate_stat(cls):
        """
        Make sure that the stat has a static name and base_tag attribute.
        """
        if not hasattr(cls, 'name'):
            raise exceptions.InvalidStatError(
                'Stats must have a static name attribute.')
        if not hasattr(cls, 'base_tag'):
            raise exceptions.InvalidStatError(
                'Stats must have a static tag attribute.')

    @classmethod
    def set_settings(cls, settings):
        """
        Set the settings of a stat.
        Passed settings are merged into the default settings of the stat.
        The settings are set on the stat class, NOT an instance of the stat.
        """
        assert set(settings.keys()).issubset(set(cls.default_settings.keys()))

        for key, value in settings.items():
            key_type = type(cls.default_settings[key])
            # cast the settings value to the type
            # specified in the default settings
            cls.settings[key] = key_type(value)

    @classmethod
    def check_availability(cls):
        """
        Check if the stat is available.
        This must raise a `permon.exceptions.StatNotAvailableError`
        if the stat is not available.
        """
        pass

    @abstractmethod
    def get_stat(self):
        """
        Get the current value of the stat.
        This must be defined by the stat creator.
        """
        pass

    @property
    @abstractmethod
    def minimum(self):
        """
        Get the minimum possible value of the stat.
        return `None` if the minimum is not predetermined.
        """
        pass

    @property
    @abstractmethod
    def maximum(self):
        """
        Get the maximum possible value of the stat.
        return `None` if the maximum is not predetermined.
        """
        pass


def _import_all_stats():
    """
    Import all stats (prepackaged ones and user defined ones).
    This must only ever be called once. Otherwise they are imported
    multiple times.
    """
    here = os.path.dirname(os.path.realpath(__file__))
    default_stat_dir = os.path.join(here, 'stats', '*.py')
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
    """
    Get all stat classes. Does not check whether the stat
    is available.
    """

    stats = MetaStat.stat_classes
    # if there are no stats registered, try importing all stats
    if len(stats) == 0:
        _import_all_stats()
        stats = sorted(stats, key=lambda stat: stat.tag)

    return stats


def get_stats_from_repr(stat_repr):
    """
    Get stat classes from a mixed string or dictionary representation
    of the stats.
    """
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
    """Verify whether all passed tags exist."""
    if not isinstance(tags, list):
        tags = [tags]

    all_tags = [stat.tag for stat in get_all_stats()]

    for tag in tags:
        if tag not in all_tags:
            raise exceptions.InvalidStatError(f'stat "{tag}" does not exist.')
