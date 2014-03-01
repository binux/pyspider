#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-15 17:27:54

import time
import socket
import cPickle
import Queue as BaseQueue
from amqplib import client_0_8 as amqp

def catch_error(func):
    def wrap(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except (amqp.AMQPConnectionException, socket.error), e:
            self.reconnect()
            raise
    return wrap

class Queue(object):
    def __init__(self, name, host="localhost", user="guest", passwd="guest", vhost="/",
                       maxsize=0):
        self.name = name
        self.host = host
        self.user = user
        self.passwd = passwd
        self.vhost = vhost
        self.maxsize = maxsize
        self.name = name

        self._last_ack = None

        self.connection = amqp.Connection(host=host,userid=user,password=passwd,virtual_host=vhost)
        self.channel = self.connection.channel()
        self.channel.queue_declare(name)
        #self.channel.queue_purge(name)

    def reconnect(self):
        self.connection = amqp.Connection(host=self.host,userid=self.user,password=self.passwd,virtual_host=self.vhost)
        self.channel = self.connection.channel()

    @catch_error
    def qsize(self):
        name, size, consumers = self.channel.queue_declare(self.name, passive=True)
        return size

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
            if timeout and time.time() - start_time >= timeout:
                raise BaseQueue.Full
            time.sleep(0.3)
        msg = amqp.Message(cPickle.dumps(obj))
        self.channel.basic_publish(msg, "", self.name)

    @catch_error
    def put_nowait(self, obj):
        if self.full():
            raise BaseQueue.Full
        msg = amqp.Message(cPickle.dumps(obj))
        self.channel.basic_publish(msg, "", self.name)

    @catch_error
    def get(self, block=True, timeout=None, ack=True):
        if not block:
            return self.get_nowait()

        start_time = time.time()
        while True:
            if timeout and time.time() - start_time >= timeout:
                raise BaseQueue.Empty
            msg = self.channel.basic_get(self.name)
            if msg is not None:
                break
            time.sleep(0.3)
        if ack:
            self.channel.basic_ack(msg.delivery_info['delivery_tag'])
        else:
            self._last_ack = msg.delivery_info['delivery_tag']
        return cPickle.loads(msg.body)

    @catch_error
    def get_nowait(self, ack=True):
        msg = self.channel.basic_get(self.name)
        if msg is None:
            raise BaseQueue.Empty
        if ack:
            self.channel.basic_ack(msg.delivery_info['delivery_tag'])
        else:
            self._last_ack = msg.delivery_info['delivery_tag']
        return cPickle.loads(msg.body)

    @catch_error
    def ack(self, id=None):
        if id is None:
            id = self._last_ack
        if id is None:
            return False
        self.channel.basic_ack(id)
        return True
