#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<17175297.hk@gmail.com>
#         http://binux.me
# Created on 2012-11-15 17:27:54

import time
import cPickle
import Queue as BaseQueue
import socket
import select
import pika
import pika.exceptions

def catch_error(func):
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (select.error, socket.error, pika.exceptions.AMQPConnectionError) as e:
            self.reconnect()
            raise
    return wrap

class Queue(object):
    Empty = BaseQueue.Empty
    Full = BaseQueue.Full
    max_timeout = 0.3

    def __init__(self, name, amqp_url='amqp://guest:guest@localhost:5672/%2F', maxsize=0):
        self.name = name
        self.amqp_url = amqp_url
        self.maxsize = maxsize

        self._last_ack = None
        self.reconnect()

    def reconnect(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(self.amqp_url))
        self.channel = self.connection.channel()
        self.channel.queue_declare(self.name)
        #self.channel.queue_purge(self.name)

    @catch_error
    def qsize(self):
        ret = self.channel.queue_declare(self.name, passive=True)
        return ret.method.message_count

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

    @catch_error
    def put(self, obj, block=True, timeout=None):
        if not block:
            return self.put_nowait()

        start_time = time.time()
        while self.full():
            lasted = time.time() - start_time
            if timeout and lasted >= timeout:
                raise BaseQueue.Full
            time.sleep(min(self.max_timeout, timeout - lasted))
        return self.channel.basic_publish("", self.name, cPickle.dumps(obj))

    @catch_error
    def put_nowait(self, obj):
        if self.full():
            raise BaseQueue.Full
        return self.channel.basic_publish("", self.name, cPickle.dumps(obj))

    @catch_error
    def get(self, block=True, timeout=None, ack=True):
        if not block:
            return self.get_nowait()

        start_time = time.time()
        while True:
            lasted = time.time() - start_time
            if timeout and lasted >= timeout:
                raise BaseQueue.Empty
            try:
                return self.get_nowait(ack)
            except BaseQueue.Empty as e:
                time.sleep(min(self.max_timeout, timeout - lasted))

    @catch_error
    def get_nowait(self, ack=True):
        method_frame, header_frame, body = self.channel.basic_get(self.name)
        if method_frame is None:
            raise BaseQueue.Empty
        if ack:
            self.channel.basic_ack(method_frame.delivery_tag)
        else:
            self._last_ack = method_frame.delivery_tag
        return cPickle.loads(body)

    @catch_error
    def ack(self, id=None):
        if id is None:
            id = self._last_ack
        if id is None:
            return False
        self.channel.basic_ack(id)
        return True

    @catch_error
    def delete(self):
        return self.channel.queue_delete(queue=self.name)
