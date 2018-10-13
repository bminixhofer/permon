import json
import os
from appdirs import user_config_dir

config_dir = user_config_dir('permon', 'bminixhofer')
config_path = os.path.join(config_dir, 'config.json')

default_config = {
    'stats': ['core.cpu_usage',
              'core.ram_usage',
              'core.read_speed',
              'core.write_speed']
}


def get_config():
    config = default_config

    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            custom_config = json.load(f)
            config = {**config, **custom_config}

    return config


def set_config(custom_config):
    assert set(custom_config.keys()).issubset(set(custom_config)), \
        'custom config keys must exist in the default config.'
    # merge custom config into default config
    config = {**default_config, **custom_config}

    os.makedirs(config_dir, exist_ok=True)
    with open(config_path, 'w') as f:
        json.dump(config, f)
