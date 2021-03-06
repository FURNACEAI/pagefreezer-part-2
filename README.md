# PageFreezer DevTest Part 2

**Website / endpoint polling daemon for determining the health of a list of URLs.**

Sure, nine urls is fine. But what about 10,000? I've expanded the JSON list with a test set of 10K sample urls. The list can be pared down at the command line with `-l <number>`. See the [Usage](#usage) section below for full details.

There are several urls in this list that are duplicates. The app doesn't regard this a problem and simply creates a new thread for each URL.

## Methodology

I decided to use a threading model with recursive functions for the core processing. In a nutshell a thread pool manager is loaded with all of the tasks and a single func `fetch_url()` is mapped to each thread with the URL and sleep time.

Is this a good idea? Good question. Certainly, not on a single CPU running on a laptop. Certainly not if you don't want a single point of failure. Is it a good idea in general? Possibly. I can't claim to be a multithreading expert. While I know cluster and distributed computing experts, I didn't consult them for this. My gut says this isn't the best method of tackling this problem but given the time constraints, this was an option that could be built.

In the end, there's a germ of an idea here that could be built upon.

Maybe.

**UPDATE:** [After a bit more research,](https://software.intel.com/en-us/articles/case-study-parallelizing-a-recursive-problem-with-intel-threading-building-blocks) it appears the pattern we've used here is fairly common in parallel processing applications.

The one major structural change that would probably be good to make is to break the bulk of the fetching code out into a non-recursive function. The rule of thumb seems to be "always reduce your work down to a non-recursive element."

By doing this we would then load the thread pool with a generic `do_work()` function that takes a func and *args and only handles the recursion. This might allow the execution time to be broken out into a decorator, for instance.

## Thread Pooling and futures

As a default I'm using [`concurrent.futures`](http://masnun.com/2016/03/29/python-a-quick-introduction-to-the-concurrent-futures-module.html) for a couple of reasons:

1) It's pretty fast in general

2) It's in the std lib starting in Python 3.4

3) asyncio isn't technically supported in Python 2.x (I don't believe) and Trollius is throwing a ton of errors that I didn't feel like debugging

An interesting limitation that I hadn't expected is that the initialization of the thread pool bottlenecks once the service start fetching urls. The thread pool increases, however, it does so very slowly since I believe the manager is busying with the fetching processes. This could probably be resolved by distributing the tasks across a cluster with [dispy](http://dispy.sourceforge.net/), [Celery](http://www.celeryproject.org/), or, possibly, a message queuing solution.

On my laptop this process bogs down on any list of urls > 4,000 items.

**UPDATE:** It's possible this bogs down because so many threads are allocated. It's written to allocate a thread for *each* URL. That may not be the best way to do that. It may be better to allocate a number of threads based on a multiple of the processor cores and let the pool manager do it's job. Would require more research into threading best practices.

Note on gevent: I wanted to compare futures and gevent in terms of performance, however, gevent doesn't like the native sleep() function. I appears to want to use gevent.sleep() and won't run the tasks acync. Support for gevent is probably out of scope for this exercise.

## Summary Stats

The assignment didn't really say where or how these should be logged so we're just going to print these to the console every n seconds. Obviously this could be customized. Summary isn't persistent, it's generated on the fly from the database log.

This isn't how I would normally build something like this. This should be in a cron job or a web dashboard so if it fails it doesn't take down the polling. However, I also wouldn't build a daemon that printed to console continuously either with a `verbose` switch, but it's a scratch test so there it is.

One note on the summary: For the stat "Largest URL delay (last 5 mins):" I'm only returning a value for a successful fetch (200), not failures.

## Usage

Entry point for this application is [app.py](https://github.com/FURNACEAI/pagefreezer-part-2/blob/master/app.py). For it to run properly, you'll need to pass in some options.

-h, --help            show this help message and exit

-s, --start           Starts the polling daemon.

-t {futures,gevent}, --threading {futures,gevent}
                      Tells the application which thread pool manager to
                      use. Defaults to "futures."

-l LIMIT, --limit LIMIT
                      Indicates how many URLs should polled. Takes
                      an int. If left empty, it will use the value in the
                      defined in the config file

-i, --viewstats       View the most recent summary stats logged to the
                      database

Note: If you don't pass in -s then the service doesn't start and will exit (relatively) quietly.

## Assumptions

Regarding the following instruction: *what URLS are currently being checked*

I took this to mean the list of the URLs being checked by the entire process, not a snapshot of URLs being processed at that instant. The later is doable using a small stateful wrapper in `fetch_url()`.

In either case, I left it off the summary stats console log as it could print out *n* URLs since I expanded the test set.

What was your intention with this request? I can build it but would need some clarification.

## Testing

> *we'd like to see some test cases for your implementation, checking the main features we outlined in the description of the problem (no need to test everything!)*

Yeah, me too. Testing recursive code -- which the bulk of this code is -- is hard even with Mock. I could add some logging nonsense specific to testing but sounds like a terrible idea.

I'll add some tests for the stats functions.

## Caveat Emptor :skull:

1) Turning off thread-safe for SQLite creates an opening for disk I/O errors (logging stats won't get written to the DB). Wouldn't happen with a real database.

2) Run this long enough with low memory and a large dataset and it will absolutely seg fault. You're welcome.

## Lessons Learned

1) https://abc.com/ doesn't resolve. Great job, ABC.

2) Shockingly light performance hit. This isn't coin mining by a long shot.

3) Tread pool manager loads about as fast as a standard list.

4) SQLite has some interesting concurrency checks that prevent it from using a single connection across multiple threads, throwing an error:
```
SQLite objects created in a thread can only be used in that same thread.The object was created in thread id 140736291423040 and this is thread id 123145510952960
```
You can disable this check by adding `check_same_thread=False` to the `.connect()` method, which I did.

# Future Improvements

1) Just realized I should destroy any URLs in the list not being used post-limit so they're not chewing up memory.

2) The summary stat "Largest URL delay (last 5 mins):" can return None if it's been more than five minutes since this was running.
