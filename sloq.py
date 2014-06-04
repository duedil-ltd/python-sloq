from Queue import Queue
from threading import Lock
import time


class TokenBucket(object):
    """TokenBucket provides a count method which offers the number of
    time-limited operations that you are able to perform and keeps track of
    this over time. Basing operations off of this allows you to determine the
    number of...

    The tokens will not begin accruing if you pass start=False, after which
    you will need to reset() the bucket to begin. Doing so allows you to
    specify the number of initial tokens available.

    tick:
        The interval in seconds between releasing new tokens
    start:
        Whether to begin ticking now
    lock:
        An optional locking mechanism. By default we using threading.Lock.
    """
    def __init__(self, tick, start=True, lock=None):
        if tick <= 0:
            raise ValueError("TokenBucket tick must be greater than 0")

        self.lock = lock or Lock()
        self.tick = tick
        self.last_tick = None
        if start:
            self.reset()

    def reset(self, tokens=0):
        self._tokens = float(tokens)
        self.last_tick = self.now()

    def now(self):
        """now returns a representation of the current time in seconds. Ideally
        it should contain partial seconds too.
        """
        return time.time()

    def count(self):
        """count returns the number of tokens available in the bucket and is
        responsible for accuring further tokens.
        """
        if not self.last_tick:
            raise RuntimeError("The TokenBucket has not been started. Call "
                               "reset() to start manually or pass start=True "
                               "in the constructor.")
        # Elapsed time
        now = self.now()
        time_delta = now - self.last_tick
        self.last_tick = now

        # Tokens accrued
        self._tokens += time_delta / self.tick

        return self._tokens

    def take(self, n=1, block=False, timeout=None):
        """take removes tokens from the bucket if there is sufficient amount.
        Returns true when the number of tokens have been taken, otherwise false

        n:
            The number of tokens to remove.
        block:
            Whether to sleep until a token next becomes available.
        timeout:
            The amount of time in seconds we're willing to sleep before a
            token becomes available. If we can determine in advance that no
            token will be available in the amount of time it takes for a token
            to become available we will fail early.
        """
        with self.lock:
            while True:
                n, count = float(n), self.count()
                if n <= count:
                    self._tokens -= n
                    return True
                elif block:
                    wait = 1 - (self._tokens % 1.0)
                    if timeout:
                        if wait > timeout - 0.01:
                            return False
                        timeout -= wait
                    time.sleep(wait)
                else:
                    return False


class SlowQueue(object):
    """SlowQueue is a wrapper around Queue.*Queue implementations which blocks
    for an amount of time to satisfy a certain release rate. The SlowQueue
    enforces blocking.

    queue:
        The optional Queue responsible for tracking the items in play. If you
        do not specify a queue of your own we will assume the FIFO Queue.Queue
        and use maxsize.
    maxsize:
        The maxsize given to the default Queue when we need to create our own.
    token_bucket:
        The optional TokenBucket responsible for locking for periods of time.
        If not provided we'll use a slowqueue.TokenBucket with release_tick.
    release_tick:
        The seconds between releasing items from the queue. Only used where a
        token_bucket is not provided.
    """
    def __init__(self, queue=None, maxsize=0, release_tick=None,
                 token_bucket=None):
        if token_bucket:
            self.token_bucket = token_bucket
            self.token_bucket.count()  # Ensure the accural has started
        elif release_tick:
            self.token_bucket = TokenBucket(release_tick)
        else:
            raise TypeError("SlowQueue requires a release_tick float or "
                            "token_bucket TokenBucket instance")
        self.queue = queue or Queue(maxsize=maxsize)

    def get(self, block=True, timeout=0):
        if not block or timeout != 0:
            raise ValueError(
                "SlowQueue works only with block=True and timeout=0"
            )
        item = self.queue.get(block=True)
        self.token_bucket.take(block=True)
        return item

    def get_nowait(self):
        return self.get(block=False)

    def qsize(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def full(self):
        return self.queue.full()

    def put(self, item, block=True, timeout=0):
        return self.queue.put(item, block=block, timeout=timeout)

    def put_nowait(self, item):
        return self.put(item, block=False)

    def task_done(self):
        return self.queue.task_done()

    def join(self):
        return self.queue.join()
