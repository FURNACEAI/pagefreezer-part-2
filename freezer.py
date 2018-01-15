#!/usr/bin/env python2.7
""" Website / endpoint polling daemon for determining the health of a list of URLs. """
__author__ = "Bryan Richard"
__license__ = "GPL"
__version__ = "0.1"
__email__ = "bryan@furnaceai.com"
__status__ = "Testing"

import concurrent.futures
import time
from time import sleep
import atexit
import cProfile
import urllib2
import datetime
import sys
import signal
from requests.exceptions import ConnectionError
import freezer_config as cfg
import json
import random
import gevent
from gevent.threadpool import ThreadPool
import sqlite3
from sqlite3 import Error

class Freezer:
    cls_urls = []
    cls_limit = cfg.app['limit']
    cls_counter = 0
    cls_threadpool = 'futures'
    cls_conn = None
    cls_stats_template = """\n%s
STATS SUMMARY
Total URLs checked: %s
Unique URLs checked: %s
Top 5 HTTP Codes (all time): %s
Largest URL delay (last 5 mins): %s
URLs in the queue: %s
%s\n
    """
    def __init__(self):
        self.set_urls()
        db = "%s/%s" % (cfg.cache['logging_directory'], cfg.cache['log_filename'])
        self.create_db_connection(db)

    def set_limit(self, limit):
        self.cls_limit = int(limit)
        return None

    def get_limit(self):
        return self.cls_limit

    def set_urls(self):
        print('Loading URL list...')
        # Might want to pass in the name of the json file
        self.cls_urls = json.load(open(cfg.cache['data_directory']+'/urls.json'))
        return None

    def get_urls(self):
        return self.cls_urls[0:self.get_limit()]

    def get_profiling(self):
        return self.cls_profile

    def set_profiling(self, p):
        self.cls_profile == p
        return None

    def set_threading(self, tp):
        # We could preform a sanity check to ensure that the threading pool option exists but we restrict that via the arguments so...
        self.cls_threadpool = tp
        return None

    def create_db_connection(self, db):
        """
        Create a database connection to the SQLite database specified by the db_file
        Parameters
        ----------
        db : string
            Location of the sqlite database file
        Returns
        -------
        None - Rather than passing around DB connections we'll just use a class attribute.
        """
        try:
            self.cls_conn = sqlite3.connect(db)
        except Error as e:
            print(e)
        return None


    def fetch_url(self, url, sleeptime=5):
        """
        Attempts to a poll a URL and logs the results to the console and a database.

        This is where the bulk of the work is done in this application. Each url that is required to be polled is bound to an insance of this function via whatever threading map library is used.

        Parameters
        ----------
        url : string
            Fully qualified URL of the website you wish to poll
        sleeptime : int
            How often to poll the URL

        Returns
        -------
        This is a recursive function and doesn't return a value.
        """
        # Normally we would probably caculate the exectuion time with a decorator, however, you can't do that with a recursive function since the end of the wrapper would never be executed due to this being a recusrive function.
        et_start = time.time()

        # DEBUG: Thread counting
        # self.cls_counter = self.cls_counter + 1
        # print(self.cls_counter)
        try:
            response = urllib2.urlopen(url, timeout=(sleeptime/2)) # Set the timeout to half of the sleep interval so the schedule isn't thrown completely out of whack on a timeout. If the delay on a page is greater than the timeout this obviously throws a false positive.
            res_bytes = sys.getsizeof(response.read())
            res_code = response.code
            print("%s - Returned HTTP code %s" % (url, response.code))
            # Only print this on a successful request
            # Format#  13/11/17 11:18:20 - http://cnn.com - 231274 Bytes
            #print("%s - %s - %s Bytes" % (datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), url, res_bytes))
        except urllib2.HTTPError as e:
            pass
            #print("%s - Returned HTTP Code: %s \n" % (url, e.code))
        except urllib2.URLError as e:
            print(e)
            #print('%s - Possible malformed URL\n' % (url))
        except requests.exceptions.RequestException as e:
            print(e)
        except:
            print("Unexpected error")
            #print(sys.exc_info()[0])
            # print("%s - Unexpected error: %s" % (url, sys.exc_info()[0]))
            raise
        et_end = time.time()
        sleep(sleeptime)
        """
        re: calling sleep() here.
        From the exercise description:
        "and keep in mind a certain degree of delay in the check is acceptable"

        I'm taking that to mean that the delay of the check can we added to the
        sleep interval. This means that a script won't run exactly at n seconds
        past the hour, but n + execution_time.

        And alternative pattern for this would be to have a *scheduler* independent
        of this function that injects a task into the executor at specific, timed
        intervals. Would require a bit more work and would likely need a check to
        determine if a thread for a particular was hung so you're instantuating
        multiple versions of the same thread.

        For the purposes of this exercise we're keeping it stuid simple.
        """

        """
        Recurrsively calling self to keep the process running forever.
        This forces the thread pool manager to manage thread allocation across
        n tasks on a finite number of threads
        """
        self.fetch_url(url, sleeptime)

    def summarize_stats(self, sleeptime):
        """
        Compiles stats from the database into a snapshot summary.

        The assignment didn't really say where or how these should be logged so we're just going to print these to the console every n seconds. Obviously this could be customized. Summary isn't persistant, it's generated from the database log.

        This isn't how I would normally build something like this. This should be in a cron job so if it fails it doesn't take down the polling. However, I also wouldn't build a daemon that printed to console continuously either, but it's a scratch test so there it is.

        Parameters
        ----------
        sleeptime : int
            How often to build the summary.

        Returns
        -------
        This is a recursive function and doesn't return a value.

         """
        sleep(sleeptime) # Don't summerize at startup

        lb = '=' * 72
        summary = self.cls_stats_template % (lb, lb, lb, lb, lb, lb, lb)
        print(summary)
        self.summarize_stats(sleeptime)

    def gevent_thread_test(self, *args):
        """ Test func for determining if gevent is loading the entire URL list """
        gevent.sleep(random.randint(0,2)*0.001)
        print('%i - %s - Task done' % (args[2], args[0]))

    def gevent_threading(self, urls):
        threads = []
        for d in urls:
            threads.append(gevent.spawn(self.fetch_url, d['url'], int(d['interval'])))
        gevent.joinall(threads)

    def futures_threading(self, urls):
        """ Loads the ThreadPoolExecutor and starts polling URLs. """
        print("Loading %s URLs into the futures thread pool..." % len(urls))
        # If you don't assign a max_workers number it appears that the pool will trim the list to a multiple of the cores. Some research is needed.
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=(len(urls)+1)) as executor: # +1 for the stats loop
                executor.submit(self.summarize_stats, int(cfg.app['stat_summary_interval']))
                [executor.submit(self.fetch_url, d['url'], int(d['interval'])) for d in urls] # JSON wasn't stored as an object but a list of dicts, hence the syntax.
        except:
            print "Unexpected error:", sys.exc_info()[0]
            raise

    def start_daemon(self):
        """
        Start the daemon in continuous mode and prints log to the console.
        """
        if self.cls_threadpool == 'gevent':
            self.gevent_threading(self.get_urls())
        else: # Default to futures
            self.futures_threading(self.get_urls())

    def signal_handler(signal, frame):
            # There's a way to shut down the ThreadPoolExecutor gracefully with .shutdown, I think, however, this would require class scope access. Which seems messy.
            print('Shutting down.')
            sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
