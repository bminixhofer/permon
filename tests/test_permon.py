import sys
import pytest
import warnings
import permon
import time
import random
import os
import secrets
from permon.frontend import native, terminal, browser
from permon.backend import Stat
from permon import exceptions, backend, config, security

FPS = 10
warnings.filterwarnings("ignore")
stat_classes = []
for stat in backend.get_all_stats():
    try:
        stat.check_availability()
    except exceptions.StatNotAvailableError:
        continue

    stat_classes.append(stat)


def check_if_valid_number(x):
    assert isinstance(x, float) or isinstance(x, int)


@pytest.mark.parametrize("cls", stat_classes)
def test_valid_values(cls):
    instance = cls(fps=FPS)

    if instance.has_contributor_breakdown:
        stat, _ = instance.get_stat()
    else:
        stat = instance.get_stat()

    check_if_valid_number(stat)


def test_stats_available():
    assert len(stat_classes) > 0


@pytest.mark.parametrize("cls", stat_classes)
def test_inherit_from_base(cls):
    assert issubclass(cls, Stat)


@pytest.mark.parametrize("cls", stat_classes)
def test_minimum_and_maximum_defined(cls):
    instance = cls(fps=FPS)

    minimum, maximum = instance.minimum, instance.maximum

    for x in [minimum, maximum]:
        if x is None:
            continue

        check_if_valid_number(x)


@pytest.mark.parametrize('app, arguments', [
    (terminal.TerminalApp, ['terminal']),
    (native.NativeApp, ['native']),
    (browser.BrowserApp, ['browser']),
])
def test_init(app, arguments, mocker):
    mocker.patch.object(sys, 'argv',  ['permon'] + arguments)
    patched_init = mocker.patch.object(app, 'initialize')

    permon.main()
    patched_init.assert_called_once()


def test_constant_secret_key():
    if os.path.exists(security.secret_path):
        os.remove(security.secret_path)
    key = security.get_secret_key()
    time.sleep(random.random())
    assert key == security.get_secret_key()


def test_constant_encryption():
    password = 'test123'
    pw_hash = security.encrypt_password(password)
    time.sleep(random.random())
    assert pw_hash == security.encrypt_password(password)


def test_set_config():
    config.reset_config()
    previous_stats = config.get_config()['stats'].copy()

    config.set_config({
        'stats': previous_stats + ['test']
    })
    assert len(config.get_config()['stats']) == len(previous_stats) + 1
    config.reset_config()


def test_set_invalid_config():
    with pytest.raises(AssertionError):
        config.set_config({
            secrets.token_hex(10): 1
        })
