#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-04-30 21:47:08

try:
    from urllib import parse as urlparse
except ImportError:
    import urlparse


def connect_message_queue(name, url=None, maxsize=0, lazy_limit=True):
    """
    create connection to message queue

    name:
        name of message queue

    rabbitmq:
        amqp://username:password@host:5672/%2F
        see https://www.rabbitmq.com/uri-spec.html
    beanstalk:
        beanstalk://host:11300/
    redis:
        redis://host:6379/db
    kombu:
        kombu+transport://userid:password@hostname:port/virtual_host
        see http://kombu.readthedocs.org/en/latest/userguide/connections.html#urls
    builtin:
        None
    """

    if not url:
        from pyspider.libs.multiprocessing_queue import Queue
        return Queue(maxsize=maxsize)

    parsed = urlparse.urlparse(url)
    if parsed.scheme == 'amqp':
        from .rabbitmq import Queue
        return Queue(name, url, maxsize=maxsize, lazy_limit=lazy_limit)
    elif parsed.scheme == 'beanstalk':
        from .beanstalk import Queue
        return Queue(name, host=parsed.netloc, maxsize=maxsize)
    elif parsed.scheme == 'redis':
        from .redis_queue import Queue
        db = parsed.path.lstrip('/').split('/')
        try:
            db = int(db[0])
        except:
            db = 0

        password = parsed.password or None

        return Queue(name, parsed.hostname, parsed.port, db=db, maxsize=maxsize, password=password, lazy_limit=lazy_limit)
    elif url.startswith('kombu+'):
        url = url[len('kombu+'):]
        from .kombu_queue import Queue
        return Queue(name, url, maxsize=maxsize, lazy_limit=lazy_limit)
    else:
        raise Exception('unknow connection url: %s', url)
