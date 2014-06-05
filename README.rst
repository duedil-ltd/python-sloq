Python Sloq
===========

A slower queue implementation, guaranteeing that tasks are processsed at a maximum rate. ``SlowQueue`` aims to be directly comparable with the Queue API so that it can be dropped in as an alternative implementation, as with LIFOQueue and PriorityQueue, but currently (as this needn't be the case) will raise additional ValueErrors if you try to pass ``block=False`` or ``timeout`` > 0 to ``get`` methods. Some slamming is possible and is controllable using the `max_slam` keyword argument on the TokenBucket or SlowQueue instance.

See following example (taken from demo_sloq.py) or the unit tests for more:

.. code-block:: python

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
      prog.add_argument("-s", type=float, default=0, metavar="MAX_SLAM",
                        help="The maximum amount of slam to allow")
      args = prog.parse_args(args)

      logger = logging.getLogger(__name__)
      logger.setLevel(logging.INFO)
      logger.addHandler(logging.StreamHandler())

      test_queue(logger, args.t, args.n, args.d, args.w, args.s)


  def test_queue(logger, tick=1, tasks=10, task_duration=0, worker_count=3,
                 slam=0):
      start_time = time.time()
      sloq = SlowQueue(release_tick=tick, max_slam=slam)

      # Begin the workers
      for w in xrange(0, worker_count):
          Thread(target=test_worker, args=(logger, start_time, sloq)).start()

      # Populate the queue
      for task in xrange(0, tasks):
          sloq.put((task, task_duration))
      for w in xrange(0, worker_count):
          sloq.put((None, None))

      sloq.join()


  def test_worker(logger, start_time, queue):
      while True:
          task, sleep = queue.get()
          if task is None:
              logger.info("%s, Done" % current_thread().name)
              queue.task_done()
              return
          else:
              logger.info("%s, Elapsed time: %0.2f, Task: %r",
                          current_thread().name, time.time() - start_time, task)
              if sleep:
                  time.sleep(sleep)
              queue.task_done()


  if __name__ == "__main__":
      main()

