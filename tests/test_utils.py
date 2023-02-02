import unittest

from wdcuration.utils import chunk


class TestWdcurationUtils(unittest.TestCase):
    def test_chunk(self):
        target = [(1, 2), (3, 4)]
        result = list(chunk([1, 2, 3, 4], 2))

        self.assertEqual(result, target)
