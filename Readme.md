# PageFreezer DevTest Part 2

Website / endpoint polling daemon for determining the health of a list of URLs.

Sure, 9 urls is fine. But what about 10,000? I've expanded the JSON list with a test set of 10K sample urls. The list can be pared down at the command line with -l <number>. See the Usage section below for full details.

There are several urls in this list that are duplicates. The app doesn't regard this a problem and simply creates a new thread for each URL.

## Methodology



## Thread Pooling and futures

As a default I'm using concurrent.futures for a couple of reasons:

1) It's plenty fast for what we're doing.

2) It is in the std lib starting in Python 3.4.

3) asyncio isn't technically supported in Python 2.x (I don't believe) and Trollius is throwing a ton of errors that I didn't feel like debugging.

An interesting limitation that I hadn't expected is that the initialization of the thread pool bottlenecks once the service start fetching urls. The thread pool increases, however, it does slow very slowly since I believe the manager is busying with the fetching processes. This could probably be resolved by distributing the tasks across a cluster with dispy, Celery, or similar tool.

On my laptop this process bogs down on any list of urls > 4,000 items.

Note on gevent: I wanted to compare futures and gevent in terms of performance, however, gevent doesn't like the native sleep() function. I appears to want to use gevent.sleep() and won't run the tasks acync. Support for gevent is probably out of scope for this exercise.

## Usage

-h, --help            show this help message and exit

-s, --start           Starts the polling daemon.

-t {futures,gevent}, --threading {futures,gevent}
                      Tells the application which thread pool manager to
                      use. Defaults to "futures."

-l LIMIT, --limit LIMIT
                      Indicates how many URLs should we should poll. Takes
                      an int. If left empty, it will use all URLs defined in
                      the JSON file (10,000+)

-i, --viewstats       View the most recent summary stats logged to the
                      database

Note: If you don't pass in -s then the service doesn't start will exit quietly.

## Assumptions

Regarding the following instruction: *what URLS are currently being checked*

I took this to mean the list of the URLs being checked by the entire process, not a snapshot of URLs being processed at that instant. That's doable using a small stateful wrapper in fetch_url(), however, given we're dealing in milliseconds at a given time I would suspect this list would often be empty.

If the assumption is wrong it can always be added in.

## Testing

> *we'd like to see some test cases for your implementation, checking the main features we outlined in the description of the problem (no need to test everything!)*

Yeah, me too. Testing asynchronous functions -- which the bulk of this code is -- is hard even with Mock.

## Lessons Learned

1) https://abc.com/ doesn't resolve. Great job, ABC.

2) Shockingly light performance hit. This isn't coin mining by a long shot.

3) Tread pool manager loads about as fast as a standard list.

4) SQLite has some interesting concurrency checks that preview it from using a single connection across multiple threads, throwing an error:
```
SQLite objects created in a thread can only be used in that same thread.The object was created in thread id 140736291423040 and this is thread id 123145510952960
```
You can disable this check by adding check_same_thread=False to the .connect() method.

Does turning off thread-safe create an opening for disk I/O errors? I'm not sure. Wouldn't happen with a real database, I suppose.
