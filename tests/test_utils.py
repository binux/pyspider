#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-01-18 16:53:49

import sys
import time
import unittest2 as unittest

from pyspider.libs import utils

class TestFetcher(unittest.TestCase):
    def test_readonlydict(self):
        data = dict(a='a', b=123)
        data['c'] = self
        data = utils.ReadOnlyDict(data)

        with self.assertRaises(Exception):
            data['d'] = 9

    def test_getitem(self):
        l = [1, 2]
        self.assertEqual(utils.getitem(l, 0), 1)
        self.assertEqual(utils.getitem(l, 1), 2)
        self.assertEqual(utils.getitem(l, 3), None)
        self.assertEqual(utils.getitem(l, 3, 9), 9)
        self.assertEqual(utils.getitem(l, 'key'), None)
        self.assertEqual(utils.getitem(l, 'key', 8), 8)
        data = dict(a='a', b=123)
        self.assertEqual(utils.getitem(data, 'a'), 'a')
        self.assertEqual(utils.getitem(data, 'b'), 123)
        self.assertEqual(utils.getitem(data, 'c'), None)
        self.assertEqual(utils.getitem(data, 'c', 9), 9)

    def test_format_data(self):
        now = time.time()
        self.assertEqual(utils.format_date(now - 30), '30 seconds ago')
        self.assertEqual(utils.format_date(now - 60), '1 minute ago')
        self.assertEqual(utils.format_date(now - 2*60), '2 minutes ago')
        self.assertEqual(utils.format_date(now - 30*60), '30 minutes ago')
        self.assertEqual(utils.format_date(now - 60*60), '1 hour ago')
        self.assertEqual(utils.format_date(1963475336), 'Mar 21, 2032 at 9:48')
        self.assertEqual(utils.format_date(now - 12*60*60), '12 hours ago')
        self.assertRegex(utils.format_date(now - 24*60*60), r'^yesterday at \d{1,2}:\d{2}$')
        self.assertRegex(utils.format_date(now - 2*24*60*60), r'^[A-Z][a-z]+ at \d{1,2}:\d{2}$')
        self.assertRegex(utils.format_date(now - 3*24*60*60), r'^[A-Z][a-z]+ at \d{1,2}:\d{2}$')
        self.assertRegex(utils.format_date(now - 4*24*60*60), r'^[A-Z][a-z]+ at \d{1,2}:\d{2}$')
        self.assertRegex(utils.format_date(now - 5*24*60*60), r'^\d{1,2}-\d{1,2} at \d{1,2}:\d{2}$')
        self.assertRegex(utils.format_date(now - 333*24*60*60), r'^\d{1,2}-\d{1,2} at \d{1,2}:\d{2}$')
        self.assertRegex(utils.format_date(now - 334*24*60*60), r'^[A-Z][a-z]+ \d{1,2}, \d{4} at \d{1,2}:\d{2}$')
