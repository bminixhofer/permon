import json
import os
import subprocess
from appdirs import user_config_dir

config_dir = user_config_dir('permon', 'bminixhofer')
config_path = os.path.join(config_dir, 'config.json')

# the default config, this is the config when the user first
# installs permon or when the config is reset
# only keys specified in this config can be set later, so there
# has to be a default value for everything
default_config = {
    'stats': [
        'core.cpu_usage',
        'core.ram_usage',
        'core.read_speed',
        'core.write_speed'
    ],
    'colors': ['#ed5565', '#ffce54', '#48cfad', '#sd9cec', '#ec87c0',
               '#fc6e51', '#a0d468', '#4fc1e9', '#ac92ec'],
    'verbose': True,
    'password': None
}


def _escape_windows_path(path):
    split_path = []
    _path = path
    while True:
        _path, directory = os.path.split(_path)

        if directory:
            split_path.append(directory)
        elif path:
            split_path.append(_path)
            break
    split_path.reverse()
    for i in range(len(split_path)):
        if ' ' in split_path[i]:
            split_path[i] = f'\"{split_path[i]}\"'
    return os.path.join(*split_path)


def parse_stats(stats):
    """
    Convert stats from a mixed string or dictionary representation
    to only dictionaries.
    """
    is_one = False
    if not isinstance(stats, list):
        is_one = True
        stats = [stats]
    else:
        stats = stats.copy()

    for i in range(len(stats)):
        if isinstance(stats[i], str):
            stats[i] = {
                'tag': stats[i],
                'settings': {}
            }
    return stats[0] if is_one else stats


def get_config():
    """Returns the user config or the default config if it does not exist."""
    config = default_config

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            custom_config = json.load(f)
            config = {**config, **custom_config}

    return config


def set_config(custom_config):
    """
    Sets the config. Only keys that exist in the default config can be set.
    custom_config is merged into the default config.
    """
    assert set(custom_config.keys()).issubset(set(default_config.keys())), \
        'custom config keys must exist in the default config.'
    # merge custom config into default config
    config = {**default_config, **custom_config}

    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)


def edit_config():
    """Opens an editor for the user to edit the config."""
    set_config(get_config())

    if os.name == 'posix':
        subprocess.call(['xdg-open', config_path])
    elif os.name == 'nt':
        escaped_config_path = _escape_windows_path(config_path)
        os.system(f'start {escaped_config_path}')
    elif os.name == 'darwin':
        subprocess.call(['open', config_path])


def show_config():
    """Shows the location and values of the current config."""
    config_str = json.dumps(get_config(), indent=4, sort_keys=True)
    print(f'Config directory: {config_dir}')
    print(f'Config path: {config_path}')
    print(f'Config: {config_str}')


def reset_config():
    """Resets the config to its default values."""
    set_config({})
