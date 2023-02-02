import unittest

from wdcuration.quickstatements import convert_date_to_quickstatements


class TestWdcurationQS(unittest.TestCase):
    def test_convert_date_to_quickstatements(self):
        target = "+2022-01-08T00:00:00Z/11"
        result = convert_date_to_quickstatements("2022-01-08")

        self.assertEqual(result, target)

        target_two = "+2022-12-25T00:00:00Z/11"
        result_monthday = convert_date_to_quickstatements(
            "12/25/2022", format="%m/%d/%Y"
        )

        self.assertEqual(result_monthday, target_two)
