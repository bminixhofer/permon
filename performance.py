#!/usr/bin/env python
from argparse import ArgumentParser
parser = ArgumentParser()
parser.add_argument('-t', '--terminal', dest='terminal', action='store_true')
args = parser.parse_args()

if args.terminal:
    import terminal_frontend
else:
    import gui_frontend
