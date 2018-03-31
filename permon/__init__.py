#!/usr/bin/env python
__version__ = '1.0.0'

def main():
    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument('-t', '--terminal', dest='terminal', action='store_true')
    args = parser.parse_args()

    if args.terminal:
        import permon.terminal_frontend
    else:
        import permon.gui_frontend


if __name__ == '__main__':
    main()
