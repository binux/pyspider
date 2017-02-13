#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-05-22 20:54:01

import time
import umsgpack
from kombu import Connection, enable_insecure_serializers
from kombu.serialization import register
from kombu.exceptions import ChannelError
from six.moves import queue as BaseQueue


register('umsgpack', umsgpack.packb, umsgpack.unpackb, 'application/x-msgpack')
enable_insecure_serializers(['umsgpack'])


class KombuQueue(object):
    """
    kombu is a high-level interface for multiple message queue backends.

    KombuQueue is built on top of kombu API.
    """

    Empty = BaseQueue.Empty
    Full = BaseQueue.Full
    max_timeout = 0.3

    def __init__(self, name, url="amqp://", maxsize=0, lazy_limit=True):
        """
        Constructor for KombuQueue

        url:        http://kombu.readthedocs.org/en/latest/userguide/connections.html#urls
        maxsize:    an integer that sets the upperbound limit on the number of
                    items that can be placed in the queue.
        """
        self.name = name
        self.conn = Connection(url)
        self.queue = self.conn.SimpleQueue(self.name, no_ack=True, serializer='umsgpack')

        self.maxsize = maxsize
        self.lazy_limit = lazy_limit
        if self.lazy_limit and self.maxsize:
            self.qsize_diff_limit = int(self.maxsize * 0.1)
        else:
            self.qsize_diff_limit = 0
        self.qsize_diff = 0

    def qsize(self):
        try:
            return self.queue.qsize()
        except ChannelError:
            return 0

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
        if self.lazy_limit and self.qsize_diff < self.qsize_diff_limit:
            pass
        elif self.full():
            raise BaseQueue.Full
        else:
            self.qsize_diff = 0
        return self.queue.put(obj)

    def get(self, block=True, timeout=None):
        try:
            ret = self.queue.get(block, timeout)
            return ret.payload
        except self.queue.Empty:
            raise BaseQueue.Empty

    def get_nowait(self):
        try:
            ret = self.queue.get_nowait()
            return ret.payload
        except self.queue.Empty:
            raise BaseQueue.Empty

    def delete(self):
        self.queue.queue.delete()

    def __del__(self):
        self.queue.close()


Queue = KombuQueue
