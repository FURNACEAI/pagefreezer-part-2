#!/usr/bin/env python2.7
"""  """
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
from requests.exceptions import ConnectionError
import freezer_config as cfg


URLS = ['http://www.foxnews.com/',
    'http://www.cnn.com/',
    'http://europe.wsj.com/',
    'http://www.bbc.co.uk/',
    'http://some-made-up-domain.com/',
    'http://some-made-up-domain.com/',
    '7 http://some-made-up-domain.com/',
    '8 http://some-made-up-domain.com/',
    '9 http://some-made-up-domain.com/',
    '10 http://some-made-up-domain.com/',
    '11 http://some-made-up-domain.com/',
    '12 http://some-made-up-domain.com/',
    '13 http://some-made-up-domain.com/',
    '14 http://some-made-up-domain.com/',
    '15 http://some-made-up-domain.com/',
    '16 http://some-made-up-domain.com/',
    '17 http://some-made-up-domain.com/',
    '18 http://some-made-up-domain.com/',
    '19 http://some-made-up-domain.com/',
    '20 http://some-made-up-domain.com/',
    '21 http://some-made-up-domain.com/',
    '22 http://some-made-up-domain.com/',
    '23 http://some-made-up-domain.com/',
    '24 http://some-made-up-domain.com/',
    '25 http://some-made-up-domain.com/']

class Freezer:
    thread_pools = ['futures', 'gevent']
    # def __init__(self):
        # Load the configuration files

    def set_profiling(self, p=FALSE): 
        self.profile == p

    def set_threading(self, tp):
        # Sanity check
        if tp in self.thread_pools:
            self.tp = tp
        else:
            # Default to futures
            self.tp = 'futures'

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
        try:
            response = urllib2.urlopen(url, timeout=(sleeptime/2)) # Set the timeout to half of the sleep interval so the schedule isn't thrown completely out of whack on a timeout. Natually, this could be further customized.
            res_bytes = sys.getsizeof(response.read())
            res_code = response.code

            # Only print this on a successful request
            # Format#  13/11/17 11:18:20 - http://cnn.com - 231274 Bytes
            print("%s - %s - %s Bytes" % (datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), url, res_bytes))
        except urllib2.HTTPError as e:
            print(e.code)
        except urllib2.URLError:
            print('Possible malformed URL - %s' % url)
        except requests.exceptions.RequestException as e:
            print(e)

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

        I normally wouldn't build this like this but it was requested in the assignment. This would be better handeled as a cron job. I might be reading the task -- "data on the status of the system should be logged every minute" -- incorrectly. Maybe this means logged to the console since it doesn't seem like this data summary needs to be persistant and could be built upon request. But, there you have it. To see a view on the summary data use the view_summary() function.

        Parameters
        ----------
        sleeptime : int
            How often to build the summary.

        Returns
        -------
        This is a recursive function and doesn't return a value.

         """

        sleep(sleeptime) # Don't summerize immediately at startup
        print("\n\n\n\n\nSummerizing the stats\n\n\n\n")
        self.summarize_stats(sleeptime)

    def view_summary(self):
        print('Here is your stat summary')


    def gevent_threading(self, urls):
        threads = []
        for i in range(1,10):
            threads.append(gevent.spawn(fetch, i))
        gevent.joinall(threads)

    def futures_threading(self, urls):
        # We're not passing in a max_workers to ThreadPoolExecutor so it will use all cores.
        with concurrent.futures.ThreadPoolExecutor() as executor:
            executor.submit(self.summarize_stats, 60)
            [executor.submit(self.fetch_url, url, 5) for url in urls]

    def start_daemon(self):
        if self.tp == 'gevent':
            self.futures_threading(urls)
        else: # Default to futures
            self.futures_threading(URLS)




#@atexit.register
#def save_cprofile_data():
#    pr.dump_stats('freezer_stats_%s.profile' % time.time())
