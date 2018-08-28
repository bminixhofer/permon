#!/usr/bin/env python
__version__ = '1.0.0'

from permon.frontend import gui, terminal

def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-t', '--terminal', dest='terminal', action='store_true')
    args = parser.parse_args()

    if args.terminal:
        terminal.main()
    else:
        gui.main()

if __name__ == '__main__':
    main()
