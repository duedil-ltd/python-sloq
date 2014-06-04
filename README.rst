Python Sloq
===========

A slower queue implementation, guaranteeing that tasks are processsed at a maximum rate. ``SlowQueue`` aims to be directly comparable with the Queue API so that it can be dropped in as an alternative implementation, as with LIFOQueue and PriorityQueue, but currently (as this needn't be the case) will raise additional ValueErrors if you try to pass ``block=False`` or ``timeout`` > 0 to ``get`` methods.

For an example, see demo_sloq.py:

.. include:: demo_sloq.py
   :code: python
