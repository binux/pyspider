#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-07 13:12:10

import heapq
import logging
import threading
import time

try:
    from UserDict import DictMixin
except ImportError:
    from collections import Mapping as DictMixin
from .token_bucket import Bucket
from six.moves import queue as Queue

logger = logging.getLogger('scheduler')

try:
    cmp
except NameError:
    cmp = lambda x, y: (x > y) - (x < y)


class AtomInt(object):
    __value__ = 0
    __mutex__ = threading.RLock()

    @classmethod
    def get_value(cls):
        cls.__mutex__.acquire()
        cls.__value__ = cls.__value__ + 1
        value = cls.__value__
        cls.__mutex__.release()
        return value


class InQueueTask(DictMixin):
    __slots__ = ('taskid', 'priority', 'exetime', 'sequence')
    __getitem__ = lambda *x: getattr(*x)
    __setitem__ = lambda *x: setattr(*x)
    __iter__ = lambda self: iter(self.__slots__)
    __len__ = lambda self: len(self.__slots__)
    keys = lambda self: self.__slots__

    def __init__(self, taskid, priority=0, exetime=0):
        self.taskid = taskid
        self.priority = priority
        self.exetime = exetime
        self.sequence = AtomInt.get_value()

    def __cmp__(self, other):
        if self.exetime == 0 and other.exetime == 0:
            diff = -cmp(self.priority, other.priority)
        else:
            diff = cmp(self.exetime, other.exetime)

        # compare in-queue sequence number finally if two element has the same
        # priority or exetime
        return diff if diff != 0 else cmp(self.sequence, other.sequence)

    def __lt__(self, other):
        return self.__cmp__(other) < 0


class PriorityTaskQueue(Queue.Queue):
    '''
    TaskQueue

    Same taskid items will been merged
    '''

    def _init(self, maxsize):
        self.queue = []
        self.queue_dict = dict()

    def _qsize(self, len=len):
        return len(self.queue_dict)

    def _put(self, item, heappush=heapq.heappush):
        if item.taskid in self.queue_dict:
            task = self.queue_dict[item.taskid]
            changed = False
            if item < task:
                changed = True
            task.priority = max(item.priority, task.priority)
            task.exetime = min(item.exetime, task.exetime)
            if changed:
                self._resort()
        else:
            heappush(self.queue, item)
            self.queue_dict[item.taskid] = item

    def _get(self, heappop=heapq.heappop):
        while self.queue:
            item = heappop(self.queue)
            if item.taskid is None:
                continue
            self.queue_dict.pop(item.taskid, None)
            return item
        return None

    @property
    def top(self):
        while self.queue and self.queue[0].taskid is None:
            heapq.heappop(self.queue)
        if self.queue:
            return self.queue[0]
        return None

    def _resort(self):
        heapq.heapify(self.queue)

    def __contains__(self, taskid):
        return taskid in self.queue_dict

    def __getitem__(self, taskid):
        return self.queue_dict[taskid]

    def __setitem__(self, taskid, item):
        assert item.taskid == taskid
        self.put(item)

    def __delitem__(self, taskid):
        self.queue_dict.pop(taskid).taskid = None


class TaskQueue(object):
    '''
    task queue for scheduler, have a priority queue and a time queue for delayed tasks
    '''
    processing_timeout = 10 * 60

    def __init__(self, rate=0, burst=0):
        self.mutex = threading.RLock()
        self.priority_queue = PriorityTaskQueue()
        self.time_queue = PriorityTaskQueue()
        self.processing = PriorityTaskQueue()
        self.bucket = Bucket(rate=rate, burst=burst)

    @property
    def rate(self):
        return self.bucket.rate

    @rate.setter
    def rate(self, value):
        self.bucket.rate = value

    @property
    def burst(self):
        return self.bucket.burst

    @burst.setter
    def burst(self, value):
        self.bucket.burst = value

    def check_update(self):
        '''
        Check time queue and processing queue

        put tasks to priority queue when execute time arrived or process timeout
        '''
        self._check_time_queue()
        self._check_processing()

    def _check_time_queue(self):
        now = time.time()
        self.mutex.acquire()
        while self.time_queue.qsize() and self.time_queue.top and self.time_queue.top.exetime < now:
            task = self.time_queue.get_nowait()  # type: InQueueTask
            task.exetime = 0
            self.priority_queue.put(task)
        self.mutex.release()

    def _check_processing(self):
        now = time.time()
        self.mutex.acquire()
        while self.processing.qsize() and self.processing.top and self.processing.top.exetime < now:
            task = self.processing.get_nowait()
            if task.taskid is None:
                continue
            task.exetime = 0
            self.priority_queue.put(task)
            logger.info("processing: retry %s", task.taskid)
        self.mutex.release()

    def put(self, taskid, priority=0, exetime=0):
        """
        Put a task into task queue
        
        when use heap sort, if we put tasks(with the same priority and exetime=0) into queue,
        the queue is not a strict FIFO queue, but more like a FILO stack.
        It is very possible that when there are continuous big flow, the speed of select is 
        slower than request, resulting in priority-queue accumulation in short time.
        In this scenario, the tasks more earlier entering the priority-queue will not get 
        processed until the request flow becomes small. 
        
        Thus, we store a global atom self increasing value into task.sequence which represent 
        the task enqueue sequence. When the comparison of exetime and priority have no 
        difference, we compare task.sequence to ensure that the entire queue is ordered.
        """
        now = time.time()

        task = InQueueTask(taskid, priority, exetime)

        self.mutex.acquire()
        if taskid in self.priority_queue:
            self.priority_queue.put(task)
        elif taskid in self.time_queue:
            self.time_queue.put(task)
        elif taskid in self.processing and self.processing[taskid].taskid:
            # force update a processing task is not allowed as there are so many
            # problems may happen
            pass
        else:
            if exetime and exetime > now:
                self.time_queue.put(task)
            else:
                task.exetime = 0
                self.priority_queue.put(task)

        self.mutex.release()

    def get(self):
        '''Get a task from queue when bucket available'''
        if self.bucket.get() < 1:
            return None
        now = time.time()
        self.mutex.acquire()
        try:
            task = self.priority_queue.get_nowait()
            self.bucket.desc()
        except Queue.Empty:
            self.mutex.release()
            return None
        task.exetime = now + self.processing_timeout
        self.processing.put(task)
        self.mutex.release()
        return task.taskid

    def done(self, taskid):
        '''Mark task done'''
        if taskid in self.processing:
            self.mutex.acquire()
            if taskid in self.processing:
                del self.processing[taskid]
            self.mutex.release()
            return True
        return False

    def delete(self, taskid):
        if taskid not in self:
            return False
        if taskid in self.priority_queue:
            self.mutex.acquire()
            del self.priority_queue[taskid]
            self.mutex.release()
        elif taskid in self.time_queue:
            self.mutex.acquire()
            del self.time_queue[taskid]
            self.mutex.release()
        elif taskid in self.processing:
            self.done(taskid)
        return True

    def size(self):
        return self.priority_queue.qsize() + self.time_queue.qsize() + self.processing.qsize()

    def is_processing(self, taskid):
        '''
        return True if taskid is in processing
        '''
        return taskid in self.processing and self.processing[taskid].taskid

    def __len__(self):
        return self.size()

    def __contains__(self, taskid):
        if taskid in self.priority_queue or taskid in self.time_queue:
            return True
        if taskid in self.processing and self.processing[taskid].taskid:
            return True
        return False


if __name__ == '__main__':
    task_queue = TaskQueue()
    task_queue.processing_timeout = 0.1
    task_queue.put('a3', 3, time.time() + 0.1)
    task_queue.put('a1', 1)
    task_queue.put('a2', 2)
    assert task_queue.get() == 'a2'
    time.sleep(0.1)
    task_queue._check_time_queue()
    assert task_queue.get() == 'a3'
    assert task_queue.get() == 'a1'
    task_queue._check_processing()
    assert task_queue.get() == 'a2'
    assert len(task_queue) == 0
