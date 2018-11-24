import json
import os
import subprocess
from appdirs import user_config_dir

config_dir = user_config_dir('permon', 'bminixhofer')
config_path = os.path.join(config_dir, 'config.json')

default_config = {
    'stats': ['core.cpu_usage',
              'core.ram_usage',
              'core.read_speed',
              'core.write_speed'],
    'colors': ['#ed5565', '#ffce54', '#48cfad', '#sd9cec', '#ec87c0',
               '#fc6e51', '#a0d468', '#4fc1e9', '#ac92ec'],
    'verbose': True,
    'password': None
}


def get_config():
    config = default_config

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            custom_config = json.load(f)
            config = {**config, **custom_config}

    return config


def set_config(custom_config):
    assert set(custom_config.keys()).issubset(set(default_config.keys())), \
        'custom config keys must exist in the default config.'
    # merge custom config into default config
    config = {**default_config, **custom_config}

    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4, sort_keys=True)


def edit_config():
    set_config(get_config())
    if os.name == 'posix':
        subprocess.call(['xdg-open', config_path])
    elif os.name == 'nt':
        subprocess.call([config_path])


def show_config():
    config_str = json.dumps(get_config(), indent=4, sort_keys=True)
    print(f'Config directory: {config_dir}')
    print(f'Config path: {config_path}')
    print(f'Config: {config_str}')


def reset_config():
    set_config({})
