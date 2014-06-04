from unittest import TestCase
from sloq import TokenBucket
import time


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
        self.assertFalse(tb.take(block=True, timeout=1))

    def test_block(self):
        tb = TokenBucket(1)
        self.assertFalse(tb.take(block=False))
        self.assertTrue(tb.take(block=True))
