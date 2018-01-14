

USAGE


Sure, 9 urls is fine. But what about 10,000? I've expanded the JSON list with a test set of 10K sample urls. The list can be pared down at the command like with -l <number>.



THREAD POOLING & FUTURES

As a default I'm using concurrent.futures for a couple of reasons:

1) It's plenty fast for what we're doing.

2) It is in the std lib starting in Python 3.4.

3) asyncio isn't technically supported in Python 2.x (I don't believe) and Trollius is throwing a ton of errors that I didn't feel like debugging.

An interesting limitation that I hadn't expected is that the initialization of the thread pool bottlenecks once the service start fetching urls. The thread pool increases, however, it does slow very slowly since I believe the manager is busying with the fetching processes. This could probably be resolved by distributing the tasks across a cluster with dispy, Celery, or similar tool.

On my laptop this process bogs down on any set of data > 4,000 URLs.

Note on gevent: I wanted to compare futures and gevent in terms of performance, however, gevent doesn't like the native sleep() function. I appears to want to use gevent.sleep() and won't run the tasks acync. Support for gevent is probably out of scope for this exercise.

SURPRISES

1) https://abc.com/ doesn't resolve. Great job, ABC.

2) Shockingly light performance hit. This isn't coin mining by a long shot.

3) Tread pool manager loads about as fast as a standard list.
