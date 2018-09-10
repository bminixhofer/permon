#!/usr/bin/env python
__version__ = '1.0.0'

from permon.frontend import native, terminal


def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-t', '--terminal', dest='terminal',
                        action='store_true')
    args = parser.parse_args()

    # determines which tags are displayed
    tags = ['core.cpu_usage',
            'core.ram_usage',
            'core.read_speed',
            'core.write_speed']

    # determines which colors are used in frontends that support custom colors
    colors = ['#ed5565', '#ffce54', '#48cfad', '#sd9cec', '#ec87c0',
              '#fc6e51', '#a0d468', '#4fc1e9', '#ac92ec']

    if args.terminal:
        app = terminal.TerminalApp(tags, colors=colors,
                                   buffer_size=500, fps=10)
    else:
        app = native.NativeApp(tags, colors=colors,
                               buffer_size=500, fps=10)
    app.initialize()


if __name__ == '__main__':
    main()
