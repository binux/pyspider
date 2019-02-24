#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import unittest

import six
from six.moves import queue as Queue

from pyspider.scheduler.task_queue import InQueueTask, TaskQueue


class TestTaskQueue(unittest.TestCase):
    """
        TestTaskQueue
    """

    def test_task_queue_in_time_order(self):
        tq = TaskQueue(rate=300, burst=1000)

        queues = dict()
        tasks = dict()

        for i in range(0, 100):
            it = InQueueTask(str(i), priority=int(i // 10), exetime=0)
            tq.put(it.taskid, it.priority, it.exetime)

            if it.priority not in queues:
                queues[it.priority] = Queue.Queue()

            q = queues[it.priority]  # type:Queue.Queue
            q.put(it)
            tasks[it.taskid] = it
            # six.print_('put, taskid=', it.taskid, 'priority=', it.priority, 'exetime=', it.exetime)
        for i in range(0, 100):
            task_id = tq.get()
            task = tasks[task_id]
            q = queues[task.priority]  # type: Queue.Queue
            expect_task = q.get()
            self.assertEqual(task_id, expect_task.taskid)
            self.assertEqual(task.priority, int(9 - i // 10))
            # six.print_('get, taskid=', task.taskid, 'priority=', task.priority, 'exetime=', task.exetime)

        self.assertEqual(tq.size(), 100)
        self.assertEqual(tq.priority_queue.qsize(), 0)
        self.assertEqual(tq.processing.qsize(), 100)
        for q in six.itervalues(queues):  # type:Queue.Queue
            self.assertEqual(q.qsize(), 0)
        pass

    pass


class TestTimeQueue(unittest.TestCase):
    def test_time_queue(self):

        # six.print_('Test time queue order by time only')

        tq = TaskQueue(rate=300, burst=1000)

        fifo_queue = Queue.Queue()

        interval = 5.0 / 1000

        for i in range(0, 20):
            it = InQueueTask(str(i), priority=int(i // 10), exetime=time.time() + (i + 1) * interval)
            tq.put(it.taskid, it.priority, it.exetime)
            fifo_queue.put(it)
            # six.print_('put, taskid=', it.taskid, 'priority=', it.priority, 'exetime=', it.exetime)

        self.assertEqual(tq.priority_queue.qsize(), 0)
        self.assertEqual(tq.processing.qsize(), 0)
        self.assertEqual(tq.time_queue.qsize(), 20)

        for i in range(0, 20):
            t1 = fifo_queue.get()
            t2 = tq.time_queue.get()
            self.assertEqual(t1.taskid, t2.taskid)
            # six.print_('get, taskid=', t2.taskid, 'priority=', t2.priority, 'exetime=', t2.exetime)
        self.assertEqual(tq.priority_queue.qsize(), 0)
        self.assertEqual(tq.processing.qsize(), 0)
        self.assertEqual(tq.time_queue.qsize(), 0)

        queues = dict()
        tasks = dict()
        for i in range(0, 20):
            priority = int(i // 10)
            it = InQueueTask(str(i), priority=priority, exetime=time.time() + (i + 1) * interval)
            tq.put(it.taskid, it.priority, it.exetime)
            tasks[it.taskid] = it

            if priority not in queues:
                queues[priority] = Queue.Queue()
            q = queues[priority]
            q.put(it)
            pass

        self.assertEqual(tq.priority_queue.qsize(), 0)
        self.assertEqual(tq.processing.qsize(), 0)
        self.assertEqual(tq.time_queue.qsize(), 20)

        time.sleep(20 * interval)
        tq.check_update()
        self.assertEqual(tq.priority_queue.qsize(), 20)
        self.assertEqual(tq.processing.qsize(), 0)
        self.assertEqual(tq.time_queue.qsize(), 0)
        for i in range(0, 20):
            taskid = tq.get()
            t1 = tasks[taskid]
            t2 = queues[t1.priority].get()
            self.assertEqual(t1.taskid, t2.taskid)

        self.assertEqual(tq.priority_queue.qsize(), 0)
        self.assertEqual(tq.processing.qsize(), 20)
        self.assertEqual(tq.time_queue.qsize(), 0)

        pass

    pass


if __name__ == '__main__':
    unittest.main()
