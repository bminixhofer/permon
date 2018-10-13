#!/usr/bin/env python
__version__ = '1.0.0'

from permon.frontend import native, terminal, browser
from permon import config, backend


def main():
    from argparse import ArgumentParser

    stat_tags = config.get_config()['stats']

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

    stat_str = ', '.join(stat_tags)
    for subparser in subparsers.choices.values():
        subparser.add_argument('stats', nargs='*', default=stat_tags, help=f"""
        which stats to display.
        If none are given, take those from the config file ({stat_str})
        """)
    args = parser.parse_args()
    stat_tags = args.stats

    stats = backend.get_stats_from_tags(stat_tags)

    # determines which colors are used in frontends that support custom colors
    colors = ['#ed5565', '#ffce54', '#48cfad', '#sd9cec', '#ec87c0',
              '#fc6e51', '#a0d468', '#4fc1e9', '#ac92ec']

    if args.frontend == 'browser':
        app = browser.BrowserApp(stats, colors=colors,
                                 buffer_size=50, fps=1,
                                 port=args.port, ip=args.ip)
    elif args.frontend == 'native':
        app = native.NativeApp(stats, colors=colors,
                               buffer_size=500, fps=10)
    elif args.frontend == 'terminal':
        app = terminal.TerminalApp(stats, colors=colors,
                                   buffer_size=500, fps=10)
    app.initialize()


if __name__ == '__main__':
    main()
