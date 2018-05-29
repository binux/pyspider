#!/usr/bin/env python
# -*- coding: utf-8 -*-


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

            six.print_('put, ', it)

        for i in range(0, 100):
            task_id = tq.get()
            task = tasks[task_id]
            q = queues[task.priority]  # type: Queue.Queue
            expect_task = q.get()
            self.assertEqual(task_id, expect_task.taskid)
            self.assertEqual(task.priority, int(9 - i // 10))
            six.print_('get, ', task)

        self.assertEqual(tq.priority_queue.qsize(), 0)
        self.assertEqual(tq.processing.qsize(), 100)
        for q in six.itervalues(queues):  # type:Queue.Queue
            self.assertEqual(q.qsize(), 0)
        pass

    pass


if __name__ == '__main__':
    unittest.main()
