# PageFreezer DevTest Part 2

**Website / endpoint polling daemon for determining the health of a list of URLs.**

Sure, 9 urls is fine. But what about 10,000? I've expanded the JSON list with a test set of 10K sample urls. The list can be pared down at the command line with -l <number>. See the [Usage](#usage) section below for full details.

There are several urls in this list that are duplicates. The app doesn't regard this a problem and simply creates a new thread for each URL.

## Methodology

Decided to use a threading model with recursive functions for the core processing. In a nutshell a thread pool manager is loaded with all of the tasks and a single func -- fetch_url() -- mapped to each thread with the URL and sleep time.

Is this a good idea? Good question. Certainly, not on a single CPU running on a laptop. Certainly not if you want don't a single point of failure. Is it a good idea in general? Possibly. I can't claim to be a multithreading expert. While I know cluster and distributed computing experts, I didn't consult them for this. My gut says this isn't the best method of tackling this problem but given the time constraints, this was an option that could be built.

In the end, there's a germ of an idea that could be built upon here.

Maybe.

## Thread Pooling and futures

As a default I'm using concurrent.futures for a couple of reasons:

1) It's pretty fast in general

2) It's in the std lib starting in Python 3.4

3) asyncio isn't technically supported in Python 2.x (I don't believe) and Trollius is throwing a ton of errors that I didn't feel like debugging

An interesting limitation that I hadn't expected is that the initialization of the thread pool bottlenecks once the service start fetching urls. The thread pool increases, however, it does so very slowly since I believe the manager is busying with the fetching processes. This could probably be resolved by distributing the tasks across a cluster with [dispy](http://dispy.sourceforge.net/), [Celery](http://www.celeryproject.org/), or, possibly, a message queing solution.

On my laptop this process bogs down on any list of urls > 4,000 items.

Note on gevent: I wanted to compare futures and gevent in terms of performance, however, gevent doesn't like the native sleep() function. I appears to want to use gevent.sleep() and won't run the tasks acync. Support for gevent is probably out of scope for this exercise.

## Usage

-h, --help            show this help message and exit

-s, --start           Starts the polling daemon.

-t {futures,gevent}, --threading {futures,gevent}
                      Tells the application which thread pool manager to
                      use. Defaults to "futures."

-l LIMIT, --limit LIMIT
                      Indicates how many URLs should polled. Takes
                      an int. If left empty, it will use all URLs defined in
                      the JSON file (10,000+)

-i, --viewstats       View the most recent summary stats logged to the
                      database

Note: If you don't pass in -s then the service doesn't start and will exit quietly.

## Assumptions

Regarding the following instruction: *what URLS are currently being checked*

I took this to mean the list of the URLs being checked by the entire process, not a snapshot of URLs being processed at that instant. The later is doable using a small stateful wrapper in fetch_url().

In either case, I left it off the summary stats console log as it could print out 1,000 URLs since I expanded the test set.

What was your intention with this request? I can build it but would need some clairification.

## Testing

> *we'd like to see some test cases for your implementation, checking the main features we outlined in the description of the problem (no need to test everything!)*

Yeah, me too. Testing recursive code -- which the bulk of this code is -- is hard even with Mock. I could add some logging nonsense specific to testing but sounds like a terrible idea.

I'll add some tests for the stats functions.

## Lessons Learned

1) https://abc.com/ doesn't resolve. Great job, ABC.

2) Shockingly light performance hit. This isn't coin mining by a long shot.

3) Tread pool manager loads about as fast as a standard list.

4) SQLite has some interesting concurrency checks that prevent it from using a single connection across multiple threads, throwing an error:
```
SQLite objects created in a thread can only be used in that same thread.The object was created in thread id 140736291423040 and this is thread id 123145510952960
```
You can disable this check by adding check_same_thread=False to the .connect() method.

# Issues

1) Turning off thread-safe for SQLite creates an opening for disk I/O errors. Wouldn't happen with a real database.

2) Just realized I should destroy any URLs in the list not being used post-limit so they're not chewing up memory. Noted for improvements.

3) The summary stat "Largest URL delay (last 5 mins):" can return None if it's been more than five minutes since this was running. Noted for improvements.

4) Run this long enough with low memory and a large dataset and it will absolutely seg fault. You're welcome.
