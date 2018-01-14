#!/usr/bin/env python2.7
"""  """
__author__ = "Bryan Richard"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "bryan@furnaceai.com"
__status__ = "Testing"

import sys
import argparse
from freezer import Freezer

def main():
    parser = argparse.ArgumentParser(description='Website / endpoint polling daemon for determining the health of a list of URLs.')

    parser.add_argument('-s', '--start', action="store_true", help='Starts the polling daemon.' )

    parser.add_argument('-p', '--profile', action="store_true", help='Profile the Freezer module with cProfile. Profile files are stores in the __performance__ director.' )

    parser.add_argument('-t', '--threading', help='Tells the application which thread pool manager to use. Defaults to "futures."', choices=['futures', 'gevent'])

    parser.add_argument('-i', '--viewstats', action="store_true", help='View the most recent summary stats logged to the database')

    args = parser.parse_args()
    f = Freezer()

    if args.viewstats:
        f.view_summary()
    if args.threading:
            f.set_threading(args.threading)
    if args.start:
        f.start_daemon()


if __name__ == "__main__":
    main()
