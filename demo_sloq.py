from argparse import ArgumentParser
from threading import Thread, current_thread
import logging
import time

from sloq import SlowQueue


def main(args=None):
    prog = ArgumentParser()
    prog.add_argument("-n", type=int, default=10, metavar="TASK_COUNT",
                      help="The number of tasks")
    prog.add_argument("-t", type=float, default=1, metavar="TASK_INTERVAL",
                      help="The tick: seconds between tasks being released")
    prog.add_argument("-w", type=int, default=3, metavar="WORKER_COUNT",
                      help="Number of workers")
    prog.add_argument("-d", type=float, default=0, metavar="TASK_DURATION",
                      help="Duration of a single task")
    args = prog.parse_args(args)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    logger.addHandler(logging.StreamHandler())

    test_queue(logger, args.t, args.n, args.d, args.w)


def test_queue(logger, tick=1, tasks=10, task_duration=0, num_workers=3):
    start_time = time.time()

    sloq = SlowQueue(release_tick=tick)
    for task in xrange(0, tasks):
        sloq.put((task, task_duration))

    workers = []
    for w in xrange(0, num_workers):
        t = Thread(target=test_queue_worker, args=(logger, start_time, sloq))
        workers.append(t)
        t.start()
        sloq.put((None, None))

    sloq.join()


def test_queue_worker(logger, start_time, queue):
    while True:
        task, sleep = queue.get()
        if task is None:
            logger.info("Thread: %s, Done" % current_thread().ident)
            queue.task_done()
            return
        else:
            logger.info("Thread: %s, Elapsed time: %0.2f, Task: %r",
                        current_thread().ident, time.time() - start_time, task)
            queue.task_done()
        if sleep:
            time.sleep(sleep)


if __name__ == "__main__":
    main()
