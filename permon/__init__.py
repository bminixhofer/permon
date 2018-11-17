#!/usr/bin/env python
__version__ = '1.0.0'

import logging
import sys
from permon.frontend import native, terminal, browser
from permon import config, backend


def parse_args(args, current_config):
    from argparse import ArgumentParser

    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest='subcommand', help="""
    the subcommand to launch.
    When terminal, browser or native, runs the respective frontend.
    When config, runs command to interact with configuration.
    """)

    subparsers.add_parser('terminal')
    subparsers.add_parser('native')
    browser_parser = subparsers.add_parser('browser')
    browser_parser.add_argument('--port', type=int, default=1234, help="""
    the port permon will listen on.
    """)
    browser_parser.add_argument('--ip', type=str, default='localhost', help="""
    the IP address permon will listen on.
    """)
    browser_parser.add_argument('--no-browser',  action='store_true', default=False, help="""
    don't open permon in a browser after startup.
    """)

    stat_str = ', '.join(current_config['stats'])
    for subparser in subparsers.choices.values():
        subparser.add_argument('stats', nargs='*', default=current_config['stats'], help=f"""
        which stats to display.
        If none are given, take those from the config file ({stat_str})
        """)
        if subparser.prog != 'permon terminal':
            # verbose logging is not possible for permon terminal
            # because it needs standard out to display stats
            subparser.add_argument('--verbose', action='store_true', default=current_config['verbose'], help=f"""
            whether to display verbose logging.
            """)

    config_parser = subparsers.add_parser('config')
    config_parser.add_argument('command', choices=['edit', 'show'], help=f"""
    which command to run.
    """)

    return parser.parse_args(args)


def main():
    current_config = config.get_config()
    args = parse_args(sys.argv[1:], current_config)

    if args.subcommand == 'config':
        if args.command == 'edit':
            config.edit_config()
        if args.command == 'show':
            config.show_config()
        sys.exit(0)

    stat_tags = args.stats
    stats = backend.get_stats_from_tags(stat_tags)

    # determines which colors are used in frontends that support custom colors
    colors = current_config['colors']

    verbose = 0 if args.subcommand == 'terminal' else args.verbose
    logging_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(format='%(asctime)s %(message)s',
                        datefmt='%d-%m-%Y %I:%M:%S %p',
                        level=logging_level)

    if args.subcommand == 'browser':
        app = browser.BrowserApp(stats, colors=colors,
                                 buffer_size=50, fps=1,
                                 port=args.port, ip=args.ip,
                                 open_browser=not args.no_browser)
    elif args.subcommand == 'native':
        app = native.NativeApp(stats, colors=colors,
                               buffer_size=500, fps=10)
    elif args.subcommand == 'terminal':
        app = terminal.TerminalApp(stats, colors=colors,
                                   buffer_size=500, fps=10)
    app.initialize()


if __name__ == '__main__':
    main()
