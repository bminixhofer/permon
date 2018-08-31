#!/usr/bin/env python
__version__ = '1.0.0'

from permon.frontend import native, terminal


def main():
    import permon.backend as backend
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-t', '--terminal', dest='terminal',
                        action='store_true')
    args = parser.parse_args()

    stat_funcs = [
        (backend.get_cpu_percent, {
            'title': 'CPU Usage in %',
            'minimum': 0,
            'maximum': 100
        }),
        (backend.get_ram, {
            'title': 'RAM Usage in MiB',
            'minimum': 0,
            'maximum': backend.TOTAL_RAM
        }),
        (backend.get_read, {
            'title': 'Read Speed in MiB / s',
            'minimum': 0,
            'maximum': None
        }),
        (backend.get_write, {
            'title': 'Write Speed in MiB / s',
            'minimum': 0,
            'maximum': None
        })
    ]

    if args.terminal:
        app = terminal.TerminalApp(stat_funcs, colors=[],
                                   buffer_size=500, fps=10)
    else:
        app = native.NativeApp(stat_funcs, colors=[],
                               buffer_size=500, fps=10)
    app.initialize()


if __name__ == '__main__':
    main()
