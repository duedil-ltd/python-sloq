from threading import Lock, Thread, current_thread
from unittest import TestCase
import os
import time

from sloq import SlowQueue, TokenBucket


class TokenBucketTest(TestCase):
    def test_count(self):
        tb = TokenBucket(0.05)
        time.sleep(0.2)
        self.assertTrue(4 <= tb.count() < 5)

    def test_false_start(self):
        tb = TokenBucket(0.05, start=False)
        self.assertRaises(RuntimeError, tb.count)
        self.assertRaises(RuntimeError, tb.take)

    def test_timeout(self):
        tb = TokenBucket(10)
        self.assertFalse(tb.take(block=True, timeout=0.1))

    def test_block(self):
        tb = TokenBucket(0.5)
        self.assertFalse(tb.take(block=False))
        self.assertTrue(tb.take(block=True))


class SlowQueueTest(TestCase):
    """SlowQueueTest tries to prove that sloq.SlowQueue ensures the items on
    its queue are read according to a maximum rate (i.e. enforces a minimum
    time between tasks being processed).
    """
    def test_release(self):
        self.assertReleaseRate(release_tick=0.1, worker_count=1, max_slam=1)

    def test_release_greater_than_exec(self):
        self.assertReleaseRate(release_tick=0.5, sleep=0.3, max_slam=1)

    def test_release_less_than_exec(self):
        self.assertReleaseRate(release_tick=0.1, sleep=0.3, max_slam=1)

    def assertReleaseRate(self, release_tick=0.1, tolerance=0.001, **kwargs):
        timer = self.time(release_tick=release_tick, **kwargs)
        self.assertLessEqual(release_tick, timer.min + tolerance)

    def time(self, queue=None, release_tick=0.1, items=None, item_count=10,
             worker_count=1, sleep=0, kill_signal=None, debug=False, **kwargs):
        """time populates a queue and creates a set of workers to process each
        of those tasks, which involves sleeping for the given amount of time.
        time returns an EventTimer giving statistics about when tasks are begun
        """
        debug = debug or os.environ.get("DEBUG")
        if queue is None:
            queue = SlowQueue(release_tick=release_tick, **kwargs)

        # Begin and time the workers
        timer = EventTimer(debug=debug)
        for w in xrange(0, worker_count):
            Thread(target=self.worker_ticker, kwargs=dict(
                queue=queue,
                timer=timer,
                sleep=sleep,
                kill_signal=kill_signal,
                debug=debug,
            )).start()

        # Reset the token bucket to account for the time taken to set up the
        # workers. We start with a negative number to create a delay before
        # tokens begin being released. We aim for this delay to be
        # approximately two seconds.
        queue.reset_tokens(tokens=-worker_count / 2.0)

        # Populate the queue
        for item in (items or xrange(0, item_count)):
            queue.put(item)
        for w in xrange(0, worker_count):
            queue.put(kill_signal)

        queue.join()
        return timer

    @staticmethod
    def worker_ticker(queue, timer, sleep=0, kill_signal=None, debug=False):
        """worker_ticker will process each item on the queue, ending when the
        task matches the kill_signal, otherwise sleeping for the defined
        time before marking the task done and processing another.
        """
        while True:
            task = queue.get(block=True)
            if task == kill_signal:
                if debug:
                    print "[%0.2f] %s: Done" % (queue.token_bucket.count(),
                                                current_thread().name)
                queue.task_done()
                return
            else:
                if debug:
                    print "[%0.2f] %s: %r" % (queue.token_bucket.count(),
                                              current_thread().name, task)
                timer.tick("None" if task is None else task)
                if sleep:
                    time.sleep(sleep)
                queue.task_done()


class EventTimer(object):
    """EventTimer will track metrics of the time between events occuring,
    offering the maximum, minimum, and average time between events. An event
    occuring is indicating by a tick.

    debug:
        Whether to print information with each tick
    discard:
        The number of records to ditch before tracking stats
    """
    def __init__(self, debug=False, discard=0):
        self.debug = debug
        self.lock = Lock()
        self.discard = discard

        self.last_tick = None
        self.count = 0
        self.sum = 0.0
        self.max = float('-infinity')
        self.min = float('infinity')

    def tick(self, msg=None):
        with self.lock:
            if self.discard > 0:
                self.discard -= 1
                if self.debug:
                    if msg:
                        print "%s %r; discarded, and next %d" % \
                              (self, msg, self.discard)
                    else:
                        print "%s; discarded, and next %d" % \
                              (self, self.discard)
                return

            now = time.time()
            if self.last_tick is None:
                self.last_tick = now
                if self.debug:
                    if msg is not None:
                        print self, msg
                    else:
                        print self
                return

            diff = now - self.last_tick
            self.count += 1
            self.sum += diff
            self.max = max(diff, self.max)
            self.min = min(diff, self.min)
            self.last_tick = now

            if self.debug:
                if msg is not None:
                    print "%s %.6f %r" % (self, diff, msg)
                else:
                    print "%s %.6f" % (self, diff)

    @property
    def avg(self):
        return self.sum / self.count

    def __str__(self):
        try:
            avg = "%.2f" % self.avg
        except:
            avg = "undefined"

        return "%s(count=%d, sum=%f, max=%f, min=%f, avg=%s)" % (
            self.__class__.__name__, self.count, self.sum, self.max, self.min,
            avg
        )
