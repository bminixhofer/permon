#!/usr/bin/env python
__version__ = '1.0.0'

from permon.frontend import native, terminal
import permon.backend as backend


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-t', '--terminal', dest='terminal',
                        action='store_true')
    args = parser.parse_args()

    tags = ['cpu_usage', 'ram_usage', 'read_speed', 'write_speed']
    stat_funcs = []
    for stat_class in backend.get_available_stats():
        if stat_class.tag in tags:
            instance = stat_class()
            stat_funcs.append((instance.get_stat, {
                'title': stat_class.name,
                'minimum': instance.minimum,
                'maximum': instance.maximum
            }))

    if args.terminal:
        app = terminal.TerminalApp(stat_funcs, colors=[],
                                   buffer_size=500, fps=10)
    else:
        app = native.NativeApp(stat_funcs, colors=[],
                               buffer_size=500, fps=10)
    app.initialize()


if __name__ == '__main__':
    main()
