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
import urllib2
import datetime
import sys
import signal
import json
import random
import sqlite3
from sqlite3 import Error
import gevent
from gevent.threadpool import ThreadPool
import freezer_config as cfg
from requests.exceptions import ConnectionError

class Freezer:
    cls_urls = []
    cls_limit = cfg.app['limit']
    cls_counter = 0
    cls_threadpool = 'futures'
    cls_conn = None
    cls_cur = None
    cls_profile = False
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
        self.__create_db_connection(db)

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
        self.cls_profile = p
        return None

    def set_threading(self, tp):
        # We could preform a sanity check to ensure that the threading pool option exists but we restrict that via the arguments so...
        self.cls_threadpool = tp
        return None

    def __setup_database(self):
        # Ha! cold_storage! Good one...
        sql = "CREATE TABLE IF NOT EXISTS cold_storage (url text NOT NULL, http_response INTEGER NOT NULL, response_time NUMERIC NOT NULL, created_on NUMERIC NOT NULL);"
        # This is a little lazy but it works.
        try:
            self.cls_conn.execute(sql)
            self.cls_conn.commit()
        except sqlite3.Error as er:
            print(er)
            print("SQLite Error: %s" % sql)
        return None

    def __create_db_connection(self, db):
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
            self.cls_conn = sqlite3.connect(db, check_same_thread=False)
            self.__setup_database()
            self.cls_cur = self.cls_conn.cursor()
        except Error as e:
            print(e)
        return None

    def __log_response(self, url, response, execution_time):
        sql = "INSERT INTO cold_storage VALUES ('%s', %s, %s, %s)" % (url, int(response), execution_time, time.time())
        try:
            self.cls_conn.execute(sql)
            self.cls_conn.commit()
        except sqlite3.Error as er:
            print(er)
            print("SQLite Error: %s" % sql)


    def __fetch_response_codes(self):
        sql = "SELECT http_response, COUNT(http_response) FROM cold_storage GROUP BY http_response ORDER BY http_response ASC LIMIT 5"
        try:
            self.cls_cur.execute(sql)
            return self.cls_cur.fetchall()
        except sqlite3.Error as er:
            print(er)
            print("SQLite Error: %s" % sql)

    def __offset_timestamp(self, min_offset):
        sec = min_offset*60
        return (time.time()-sec)

    def __fetch_max_response_time(self):
        sql = "SELECT url, MAX(response_time) FROM 'cold_storage' WHERE created_on > %s AND http_response = 200" % self.__offset_timestamp(5)
        try:
            self.cls_cur.execute(sql)
            return self.cls_cur.fetchone()
        except sqlite3.Error as er:
            print(er)
            print("SQLite Error: %s" % sql)

    def __fetch_total_requests(self):
        sql = "SELECT COUNT (url) FROM 'cold_storage'"
        try:
            self.cls_cur.execute(sql)
            return self.cls_cur.fetchone()
        except sqlite3.Error as er:
            print(er)
            print("SQLite Error: %s" % sql)

    def __fetch_total_unique_request(self):
        sql = "SELECT COUNT (DISTINCT url) FROM 'cold_storage'"
        try:
            self.cls_cur.execute(sql)
            return self.cls_cur.fetchone()
        except sqlite3.Error as er:
            print(er)
            print("SQLite Error: %s" % sql)

    def __fetch_url(self, url, sleeptime=5):
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
            response_code = response.code
            # Only print this on a successful request
            # Format#  13/11/17 11:18:20 - http://cnn.com - 231274 Bytes
            print("%s - %s - %s Bytes" % (datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), url, res_bytes))
        except urllib2.HTTPError as e:
            reponse_code = e.code
        except urllib2.URLError as e:
            response_code = 418 # Made up code for DNS failure
        except requests.exceptions.RequestException as e:
            print(e)
        except:
            print("%s - Unexpected error: %s" % (url, sys.exc_info()[0]))
            raise
        et_end = time.time()

        self.__log_response(url, response_code, et_end - et_start)
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

        Recurrsively calling self to keep the process running forever.
        This forces the thread pool manager to manage thread allocation across
        n tasks on a finite number of threads
        """
        self.__fetch_url(url, sleeptime)

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

        # Fetch and format the HTTP response code logs
        rc = self.__fetch_response_codes()
        rcf = ""
        for c, n in rc:
            rcf = rcf + "%s (%s)   " % (c, n)

        # Format response time value
        response_time = self.__fetch_max_response_time()
        response_time = "%s (%s seconds)" % (response_time[0], response_time[1])

        summary = self.cls_stats_template % (lb, self.__fetch_total_requests()[0], self.__fetch_total_unique_request()[0], rcf, response_time, len(self.get_urls()), lb)
        print(summary)
        if sleeptime > 0:
            self.summarize_stats(sleeptime)

    def __gevent_thread_test(self, *args):
        """ Test func for determining if gevent is loading the entire URL list """
        gevent.sleep(random.randint(0,2)*0.001)
        print('%i - %s - Task done' % (args[2], args[0]))

    def __gevent_threading(self, urls):
        threads = []
        for d in urls:
            threads.append(gevent.spawn(self.__fetch_url, d['url'], int(d['interval'])))
        gevent.joinall(threads)

    def futures_threading(self, urls):
        """ Loads the ThreadPoolExecutor and starts polling URLs. """
        print("Loading %s URLs into the futures thread pool..." % len(urls))
        # If you don't assign a max_workers number it appears that the pool will trim the list to a multiple of the cores. Some research is needed.
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=(len(urls)+1)) as executor: # +1 for the stats loop
                executor.submit(self.summarize_stats, int(cfg.app['stat_summary_interval']))
                threads = [executor.submit(self.__fetch_url, d['url'], int(d['interval'])) for d in urls] # JSON wasn't stored as an object but a list of dicts, hence the syntax.
        except:
            print("Unexpected error: %s" % (sys.exc_info()[0]))
            raise

    def start_daemon(self):
        """
        Start the daemon in continuous mode and prints log to the console.
        """
        if self.cls_threadpool == 'gevent':
            self.__gevent_threading(self.get_urls())
        else: # Default to futures
            self.futures_threading(self.get_urls())

    def signal_handler(self, signal, frame):
        # There's a way to shut down the ThreadPoolExecutor gracefully with .shutdown, I think, however, this would require class scope access. Which seems messy.
        print('Shutting down.')
        sys.exit(0)
    signal.signal(signal.SIGINT, signal_handler)
