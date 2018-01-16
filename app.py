#!/usr/bin/env python2.7
__author__ = "Bryan Richard"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "bryan@furnaceai.com"
__status__ = "Testing"

import argparse
from freezer import Freezer

def main():
    parser = argparse.ArgumentParser(description="""Website / endpoint polling
    daemon for determining the health of a list of URLs.""")

    parser.add_argument('-s', '--start', action="store_true", help="""Starts the
     polling daemon.""")

    parser.add_argument('-t', '--threading', help="""Tells the application which
     thread pool manager to use. Defaults to "futures." """, choices=['futures', 'gevent'])

    parser.add_argument('-l', '--limit', type=int, help="""Indicates how many
    URLs we should poll. Takes an int. If left empty, it will use the value in
    the defined in the config file""")

    parser.add_argument('-i', '--viewstats', action="store_true", help="""View
    the most recent summary stats logged to the database""")

    parser.add_argument('-d', '--debug', action="store_true", help="""Testing
    hook for scratch debuggign work.""")

    args = parser.parse_args()
    freezer = Freezer()

    if args.limit:
        freezer.set_limit(args.limit)
    if args.threading:
        freezer.set_threading(args.threading)
    if args.viewstats:
        freezer.summarize_stats(0)
    if args.debug:
        freezer.process_thread(freezer.debug, ('foo', 'bar'))
    if args.start:
        freezer.start_daemon()

if __name__ == "__main__":
    main()
