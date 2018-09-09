import sys
import pytest
import numpy as np
import permon
from permon.frontend import native, terminal
import permon.backend as backend
from permon.classes import Stat

stat_classes = backend.get_available_stats()


def check_if_valid_number(x):
    assert not np.isnan(x)
    assert isinstance(x, float) or isinstance(x, int)


@pytest.mark.parametrize("cls", stat_classes)
def test_valid_values(cls):
    instance = cls()
    stat = instance.get_stat()
    check_if_valid_number(stat)

    instance.destruct()


def test_stats_available():
    assert len(stat_classes) > 0


@pytest.mark.parametrize("cls", stat_classes)
def test_inherit_from_base(cls):
    assert issubclass(cls, Stat)


@pytest.mark.parametrize("cls", stat_classes)
def test_minimum_and_maximum_defined(cls):
    instance = cls()
    minimum, maximum = instance.minimum, instance.maximum

    for x in [minimum, maximum]:
        if x is None:
            continue

        check_if_valid_number(x)


@pytest.mark.parametrize('app, arguments', [
    (terminal.TerminalApp, ['-t']),
    (native.NativeApp, []),
])
def test_init(app, arguments, mocker):
    mocker.patch.object(sys, 'argv',  ['permon'] + arguments)
    patched_init = mocker.patch.object(app, 'initialize')

    permon.main()
    patched_init.assert_called_once()
