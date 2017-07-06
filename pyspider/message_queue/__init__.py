#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-04-30 21:47:08

import logging

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
        redis://host1:port1,host2:port2,...,hostn:portn (for redis 3.x in cluster mode)
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
        if ',' in parsed.netloc:
            """
            redis in cluster mode (there is no concept of 'db' in cluster mode)
            ex. redis://host1:port1,host2:port2,...,hostn:portn
            """
            cluster_nodes = []
            for netloc in parsed.netloc.split(','):
                cluster_nodes.append({'host': netloc.split(':')[0], 'port': int(netloc.split(':')[1])})

            return Queue(name=name, maxsize=maxsize, lazy_limit=lazy_limit, cluster_nodes=cluster_nodes)

        else:
            db = parsed.path.lstrip('/').split('/')
            try:
                db = int(db[0])
            except:
                logging.warning('redis DB must zero-based numeric index, using 0 instead')
                db = 0

            password = parsed.password or None

            return Queue(name=name, host=parsed.hostname, port=parsed.port, db=db, maxsize=maxsize, password=password, lazy_limit=lazy_limit)
    elif url.startswith('kombu+'):
        url = url[len('kombu+'):]
        from .kombu_queue import Queue
        return Queue(name, url, maxsize=maxsize, lazy_limit=lazy_limit)
    else:
        raise Exception('unknown connection url: %s', url)
