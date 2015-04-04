#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-04-05 00:05:58

import sys
import time
import unittest2 as unittest

from pyspider.libs import counter

class TestCounter(unittest.TestCase):
    def test_TimebaseAverageEventCounter(self):
        c = counter.TimebaseAverageEventCounter(2, 1)
        for i in range(100):
            time.sleep(0.1)
            c.event(100+i)
        self.assertEqual(c.sum, float(180+199)*20/2)
        self.assertEqual(c.avg, float(180+199)/2)
