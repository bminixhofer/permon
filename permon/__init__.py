#!/usr/bin/env python

import logging
import sys
import os
import json
import textwrap
import permon
from permon.frontend import native, terminal, browser
from permon import config, backend, exceptions, security

here = os.path.abspath(os.path.dirname(__file__))
__version__ = open(os.path.join(here, 'VERSION')).read()


def get_parser(current_config=None):
    from argparse import ArgumentParser

    if current_config is None:
        current_config = config.get_config()

    parser = ArgumentParser(description="""
A tool to display live line charts in a clear, uncluttered way.
Source code is available at https://github.com/bminixhofer/permon.
See the documentation at https://bminixhofer.github.io/permon/documentation
for details.
    """)
    parser.add_argument('--version', action='store_true', default=False, help="""
show permon's version and exit
    """)

    subparsers = parser.add_subparsers(dest='subcommand', help="""
the subcommand to launch.

When ``terminal``, ``browser`` or ``native``, runs the respective frontend.

When ``config``, runs command to interact with configuration.

When ``password``, runs command to set permon's password.
    """)

    subparsers.add_parser('terminal', help="""
Starts permon's terminal frontend.
    """)
    subparsers.add_parser('native', help="""
Starts permon's native frontend.
    """)
    browser_parser = subparsers.add_parser('browser', help="""
Starts permon's browser frontend.
    """)
    browser_parser.add_argument('--port', type=int, default=1234, help="""
the port permon will listen on
    """)
    browser_parser.add_argument('--ip', type=str, default='localhost', help="""
the IP address permon will listen on
    """)
    browser_parser.add_argument('--no-browser',  action='store_true', default=False, help="""
don't open permon in a browser after startup
    """)
    browser_parser.add_argument('--certfile', type=str, help="""
the path to an SSL/TLS certificate file
    """)
    browser_parser.add_argument('--keyfile', type=str, help="""
the path to a private key file for usage with SSL/TLS
    """)

    # stats in the config need to be parsed to dictionaries first
    # because they can be specified by their tag name when the settings are
    # kept at their default
    stat_tags = [x['tag'] for x in config.parse_stats(current_config['stats'])]
    stat_str = ', '.join(stat_tags)
    for subparser in subparsers.choices.values():
        subparser.add_argument('stats', nargs='*', default=current_config['stats'], help=f"""
which stats to display
If none are given, take those from the config file ({stat_str})
        """)
        subparser.add_argument('--fps', type=int, help="""
the frames per second the display moves with
        """)
        if subparser.prog != 'permon terminal':
            # verbose logging is not possible for permon terminal
            # because it needs standard out to display stats
            subparser.add_argument('--verbose', action='store_true', default=current_config['verbose'], help=f"""
whether to enable verbose logging
            """)
            # the buffer size is determined by the terminal width in the
            # terminal frontend and can thus not be set by the user
            subparser.add_argument('--buffer-size', type=int, help="""
the number of points displayed on the screen at any time
            """)

    config_parser = subparsers.add_parser('config', help=f"""
Command to interact with the configuration of permon.
Default configuration:

.. code-block:: javascript

{textwrap.indent(json.dumps(config.default_config, indent=4), ' ' * 4)}

Stats can either be specified by their tag name like in the default config or
by a dictionary with keys ``tag`` and ``settings`` where ``settings`` is a
dictionary consisting of keys and values specifying the value of settings
for the respective stat e. g.

.. code-block:: javascript

        ...
        "stats": [
            {{
                "tag": "jupyter.ram_usage",
                "settings": {{
                    "connection info": "",
                    "query interval [s]": 1
                }}
            }}
        ]
        ...

    """)
    config_parser.add_argument('command', choices=['edit', 'show', 'reset'], help=f"""
Which command to run.

When ``edit``, opens your preferred editor to edit the config.json file.

When ``show``, prints your current configuriation file and directory.

When ``reset``, resets configuration to the defaults.
    """)

    subparsers.add_parser('password', help="""
Open dialog to set permon's password.
The password is currently only used for authentication in the browser frontend.
    """)
    return parser


def main():
    current_config = config.get_config()

    parser = get_parser(current_config)
    args = parser.parse_args()

    if args.version:
        print(permon.__version__)
        sys.exit(0)

    if args.subcommand == 'config':
        if args.command == 'edit':
            config.edit_config()
        if args.command == 'show':
            config.show_config()
        if args.command == 'reset':
            config.reset_config()
        sys.exit(0)

    if args.subcommand == 'password':
        security.prompt_password()
        sys.exit(0)

    if args.subcommand is None:
        parser.print_help()
        sys.exit(1)

    # get the stat classes from the dictionaries representing stats
    stats = backend.get_stats_from_repr(args.stats)

    # determines which colors are used in frontends that support custom colors
    colors = current_config['colors']

    verbose = 0 if args.subcommand == 'terminal' else args.verbose
    logging_level = logging.INFO if verbose else logging.WARNING
    logging.basicConfig(format='%(asctime)s \t %(message)s',
                        datefmt='%d-%m-%Y %I:%M:%S %p',
                        level=logging_level)

    # instantiate the appropriate frontend depending on the frontend argument
    # specified by the user
    # instantiating the app only sets some values
    # the actual UI is launched in app.initialize
    if args.subcommand == 'browser':
        # set the ssl context if a certfile and keyfile are given for https
        ssl_context = None
        if args.certfile and args.keyfile:
            ssl_context = (args.certfile, args.keyfile)
        if bool(args.certfile) != bool(args.keyfile):
            raise ValueError(
                'either certfile and keyfile or none of both must be supplied.'
            )

        app = browser.BrowserApp(stats, colors=colors,
                                 buffer_size=args.buffer_size, fps=args.fps,
                                 port=args.port, ip=args.ip,
                                 open_browser=not args.no_browser,
                                 ssl_context=ssl_context)
    elif args.subcommand == 'native':
        app = native.NativeApp(stats, colors=colors,
                               buffer_size=args.buffer_size, fps=args.fps)
    elif args.subcommand == 'terminal':
        app = terminal.TerminalApp(stats, fps=args.fps)

    # app.make_available checks if the app is available
    # i. e. all needed modules are installed and prompts the user to
    # install them if they are not
    try:
        app.make_available()
    except exceptions.FrontendNotAvailableError as e:
        logging.error(
            f'frontend "{args.subcommand}" is not available. Reason: {str(e)}')
        sys.exit(1)

    app.initialize()


if __name__ == '__main__':
    main()
