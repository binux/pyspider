#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-07 10:33:38

import time
import unittest

from libs import utils
from libs import rabbitmq

class TestRabbitMQ(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        with utils.timeout(3):
            self.q1 = rabbitmq.Queue('test_queue', maxsize=5)
            self.q2 = rabbitmq.Queue('test_queue', maxsize=5)

    @classmethod
    def tearDownClass(self):
        self.q2.delete()
        del self.q1
        del self.q2

    def test_10_put(self):
        self.assertEqual(self.q1.qsize(), 0)
        self.assertEqual(self.q2.qsize(), 0)
        self.q1.put('TEST_DATA1', timeout=3)
        self.q1.put('TEST_DATA2', timeout=3)
        time.sleep(0.01)
        self.assertEqual(self.q1.qsize(), 2)
        self.assertEqual(self.q2.qsize(), 2)

    def test_20_get(self):
        self.assertEqual(self.q1.get(timeout=0.01), 'TEST_DATA1')
        self.assertEqual(self.q2.get_nowait(), 'TEST_DATA2')
        with self.assertRaises(self.q1.Empty):
            self.q2.get(timeout=0.01)
        with self.assertRaises(self.q1.Empty):
            self.q2.get_nowait()

    def test_30_full(self):
        self.assertEqual(self.q1.qsize(), 0)
        self.assertEqual(self.q2.qsize(), 0)
        for i in range(2):
            self.q1.put_nowait('TEST_DATA%d' % i)
        for i in range(3):
            self.q2.put('TEST_DATA%d' % i)
        with self.assertRaises(self.q1.Full):
            self.q1.put('TEST_DATA6', timeout=0.01)
        with self.assertRaises(self.q1.Full):
            self.q1.put_nowait('TEST_DATA6')
