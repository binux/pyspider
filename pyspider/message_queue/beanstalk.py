#!/usr/bin/env python
# coding:utf-8
"""beanstalk queue - queue based on beanstalk


Setting: you need to set max-job-size bigger(default 65535)
DAEMON_OPTS="-l $BEANSTALKD_LISTEN_ADDR -p $BEANSTALKD_LISTEN_PORT -z 524288"
"""

import time
import umsgpack
import beanstalkc
import threading
import logging

from six.moves import queue as BaseQueue


class BeanstalkQueue(object):
    max_timeout = 0.3
    Empty = BaseQueue.Empty
    Full = BaseQueue.Full

    def __init__(self, name, host='localhost:11300', maxsize=0):
        """
        Constructor for a BeanstalkdQueue.
        """
        self.name = name

        config = host.split(':')
        self.host = config[0] if len(config) else 'localhost'
        self.port = int(config[1]) if len(config) > 1 else 11300
        self.lock = threading.RLock()
        self.maxsize = maxsize
        self.reconnect()

    def stats(self):
        try:
            with self.lock:
                stats = self.connection.stats_tube(self.name)
        except beanstalkc.CommandFailed as err:
            # tube is empty
            if err[1] == 'NOT_FOUND':
                return {}

        stats = [item.split(': ') for item in stats.split('\n') if item.find(':')]
        stats = [(item[0], item[1]) for item in stats if len(item) == 2]
        return dict(stats)

    def reconnect(self):
        self.connection = beanstalkc.Connection(host=self.host, port=self.port, parse_yaml=False)
        self.connection.use(self.name)
        self.connection.watch(self.name)

    def qsize(self):
        stats = self.stats()
        return int(stats.get('current-jobs-ready', 0))

    def empty(self):
        if self.qsize() == 0:
            return True
        else:
            return False

    def full(self):
        if self.maxsize and self.qsize() >= self.maxsize:
            return True
        else:
            return False

    def put(self, obj, block=True, timeout=None):
        if not block:
            return self.put_nowait(obj)

        start_time = time.time()
        while True:
            try:
                return self.put_nowait(obj)
            except BaseQueue.Full:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

    def put_nowait(self, obj):
        if self.full():
            raise BaseQueue.Full

        with self.lock:
            return self.connection.put(umsgpack.packb(obj))

    def get(self, block=True, timeout=None):
        if not block:
            return self.get_nowait()

        start_time = time.time()
        while True:
            try:
                return self.get_nowait()
            except BaseQueue.Empty:
                if timeout:
                    lasted = time.time() - start_time
                    if timeout > lasted:
                        time.sleep(min(self.max_timeout, timeout - lasted))
                    else:
                        raise
                else:
                    time.sleep(self.max_timeout)

    def get_nowait(self):
        try:
            with self.lock:
                job = self.connection.reserve(0)
                if not job:
                    raise BaseQueue.Empty
                else:
                    body = umsgpack.unpackb(job.body)
                    job.delete()
                    return body
        except beanstalkc.DeadlineSoon:
            raise BaseQueue.Empty


Queue = BeanstalkQueue
