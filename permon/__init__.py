#!/usr/bin/env python
__version__ = '1.0.0'

from permon.frontend import native, terminal, browser
from permon import config, backend, exceptions


def main():
    from argparse import ArgumentParser

    monitors = config.get_config()['monitors']

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='frontend', help="""
    which frontend to use. One of terminal, native or browser.
    """)

    subparsers.add_parser('terminal')
    subparsers.add_parser('native')
    browser_parser = subparsers.add_parser('browser')
    browser_parser.add_argument('--port', type=int, default=1234, help="""
    The port permon will listen on.
    """)
    browser_parser.add_argument('--ip', type=str, default='localhost', help="""
    The IP address permon will listen on.
    """)

    parser.add_argument('monitors', nargs='*', default=monitors, help=f"""
    which monitors to display.
    If none are given, take those from the config file ({', '.join(monitors)})
    """)
    parser.add_argument('-s', '--store_config', dest='store_config',
                        action='store_true', help=f"""
    store the monitors passed to the monitors argument in the configuration.
    They will be shown per default on the next start of permon.
    """)
    args = parser.parse_args()

    monitors = args.monitors

    all_stats = [x.get_full_tag() for x in backend.get_all_stats()]
    for tag in monitors:
        if tag not in all_stats:
            raise exceptions.InvalidStatError(f'stat "{tag}" does not exist.')

    if args.store_config:
        config.set_config({
            'monitors': monitors
        })

    # determines which colors are used in frontends that support custom colors
    colors = ['#ed5565', '#ffce54', '#48cfad', '#sd9cec', '#ec87c0',
              '#fc6e51', '#a0d468', '#4fc1e9', '#ac92ec']

    if args.frontend == 'browser':
        app = browser.BrowserApp(monitors, colors=colors,
                                 buffer_size=500, fps=1,
                                 port=args.port, ip=args.ip)
    elif args.frontend == 'native':
        app = native.NativeApp(monitors, colors=colors,
                               buffer_size=500, fps=10)
    elif args.frontend == 'terminal':
        app = terminal.TerminalApp(monitors, colors=colors,
                                   buffer_size=500, fps=10)
    app.initialize()


if __name__ == '__main__':
    main()
