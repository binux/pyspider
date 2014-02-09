#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 22:37:13

import time
import unittest
from scheduler.task_queue import TaskQueue
from scheduler.token_bucket import Bucket


class TestTaskQueue(unittest.TestCase):
    def setUp(self):
        pass

    def test_task_queue(self):
        task_queue = TaskQueue()
        task_queue.processing_timeout = 0.1
        task_queue.put('a3', 3, time.time()+0.1)
        task_queue.put('a1', 1)
        task_queue.put('a2', 2)

        # priority queue
        self.assertEqual(task_queue.get(), 'a2')

        # time queue
        time.sleep(0.1)
        task_queue._check_time_queue()
        self.assertEqual(task_queue.get(), 'a3')
        self.assertEqual(task_queue.get(), 'a1')

        # processing queue
        task_queue._check_processing()
        self.assertEqual(task_queue.get(), 'a2')
        self.assertEqual(len(task_queue), 0)

        # done
        task_queue.done('a2')
        task_queue.done('a1')
        time.sleep(0.1)
        task_queue._check_processing()
        task_queue._check_time_queue()
        self.assertEqual(task_queue.get(), 'a3')
        self.assertEqual(task_queue.get(), None)


class TestBucket(unittest.TestCase):
    def test_bucket(self):
        bucket = Bucket(100, 1000)
        self.assertEqual(bucket.get(), 1000)
        time.sleep(0.1)
        self.assertEqual(bucket.get(), 1000)
        bucket.desc(100)
        self.assertEqual(bucket.get(), 900)
        time.sleep(0.1)
        self.assertAlmostEqual(bucket.get(), 910, 0)
        time.sleep(0.1)
        self.assertAlmostEqual(bucket.get(), 920, 0)


if __name__ == '__main__':
    unittest.main()
