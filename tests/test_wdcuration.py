#!/usr/bin/env python

"""Tests for `wdcuration` package."""


import unittest

import wdcuration as wd


class TestWdcuration(unittest.TestCase):
    """Tests for `wdcuration` package."""

    def test_get_list(self):
        target = ["1.C.110.1.1"]
        result = wd.wdcuration.get_statement_values("Q283350", "P7260")
        assert target == result

    def test_get_list_with_label(self):
        target = [{"id": "Q8054", "label": "protein"}]
        result = wd.wdcuration.get_statement_values("Q283350", "P31", label=True)
        assert target == result

    def tearDown(self):
        """Tear down test fixtures, if any."""

    def test_000_something(self):
        """Test something."""
