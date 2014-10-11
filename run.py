#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-03-05 00:11:49

import os
import sys
import time
import logging
import logging.config
logging.config.fileConfig("logging.conf")

from database import connect_database
from libs.utils import run_in_thread, run_in_subprocess

class Get(object):
    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter()

# config form environment -------------------
class g(object):
    scheduler_xmlrpc_port = int(os.environ.get('SCHEDULER_XMLRPC_PORT', 23333))
    fetcher_xmlrpc_port = int(os.environ.get('FETCHER_XMLRPC_PORT', 24444))
    webui_host = os.environ.get('WEBUI_HOST', '0.0.0.0')
    webui_port = int(os.environ.get('WEBUI_PORT', 5000))
    debug = bool(os.environ.get('DEBUG'))
    queue_maxsize = int(os.environ.get('QUEUE_MAXSIZE', 100))

    # databases
    if os.environ.get('MYSQL_NAME'):
        taskdb = Get(lambda : connect_database(
                'mysql+taskdb://%(MYSQL_PORT_3306_TCP_ADDR)s'
                ':%(MYSQL_PORT_3306_TCP_PORT)s/taskdb' % os.environ))
        projectdb = Get(lambda : connect_database(
            'mysql+projectdb://%(MYSQL_PORT_3306_TCP_ADDR)s'
            ':%(MYSQL_PORT_3306_TCP_PORT)s/projectdb' % os.environ))
    elif os.environ.get('TASKDB'):
        taskdb = Get(lambda : connect_database(os.environ['TAKDB']))
        projectdb = Get(lambda : connect_database(os.environ['PROJECTDB']))
    else:
        taskdb = Get(lambda : connect_database('sqlite+taskdb:///data/task.db'))
        projectdb = Get(lambda : connect_database('sqlite+projectdb:///data/project.db'))

    # queue
    if os.environ.get('RABBITMQ_NAME'):
        from libs.rabbitmq import Queue
        amqp_url = ("amqp://guest:guest@%(RABBITMQ_PORT_5672_TCP_ADDR)s"
                    ":%(RABBITMQ_PORT_5672_TCP_PORT)s/%%2F" % os.environ)
        amqp = lambda name: Queue(name, amqp_url=amqp_url, maxsize=queue_maxsize)
        newtask_queue = Get(lambda : amqp("newtask_queue"))
        status_queue = Get(lambda : amqp("status_queue"))
        scheduler2fetcher = Get(lambda : amqp("scheduler2fetcher"))
        fetcher2processor = Get(lambda : amqp("fetcher2processor"))
    else:
        from multiprocessing import Queue
        newtask_queue = Queue(queue_maxsize)
        status_queue = Queue(queue_maxsize)
        scheduler2fetcher = Queue(queue_maxsize)
        fetcher2processor = Queue(queue_maxsize)

    # scheduler_rpc
    if os.environ.get('SCHEDULER_NAME'):
        import xmlrpclib
        scheduler_rpc = Get(lambda : xmlrpclib.ServerProxy('http://%s:%s' % (
            os.environ['SCHEDULER_PORT_%d_TCP_ADDR' % scheduler_xmlrpc_port],
            os.environ['SCHEDULER_PORT_%d_TCP_PORT' % scheduler_xmlrpc_port]),
            allow_none=True))
    else:
        scheduler_rpc = None

# run commands ------------------------------------------
def run_scheduler():
    from scheduler import Scheduler
    scheduler = Scheduler(taskdb=g.taskdb, projectdb=g.projectdb,
            newtask_queue=g.newtask_queue, status_queue=g.status_queue,
            out_queue=g.scheduler2fetcher)

    run_in_thread(scheduler.xmlrpc_run, port=g.scheduler_xmlrpc_port, bind=g.webui_host)
    scheduler.run()

def run_fetcher():
    from fetcher.tornado_fetcher import Fetcher
    fetcher = Fetcher(inqueue=g.scheduler2fetcher, outqueue=g.fetcher2processor)

    run_in_thread(fetcher.xmlrpc_run, port=g.fetcher_xmlrpc_port, bind=g.webui_host)
    fetcher.run()

def run_processor():
    from processor import Processor
    processor = Processor(projectdb=g.projectdb,
            inqueue=g.fetcher2processor, status_queue=g.status_queue,
            newtask_queue=g.newtask_queue)
    
    processor.run()

def run_webui():
    import cPickle as pickle

    from webui.app import app
    app.config['taskdb'] = g.taskdb
    app.config['projectdb'] = g.projectdb
    app.config['scheduler_rpc'] = g.scheduler_rpc
    #app.config['cdn'] = '//cdnjs.cloudflare.com/ajax/libs/'
    app.run(host=g.webui_host, port=g.webui_port)

def all_in_one():
    import xmlrpclib
    g.scheduler_rpc = xmlrpclib.ServerProxy(
            'http://localhost:%d' % g.scheduler_xmlrpc_port)

    threads = []
    threads.append(run_in_subprocess(run_fetcher))
    threads.append(run_in_subprocess(run_processor))
    threads.append(run_in_subprocess(run_scheduler))
    threads.append(run_in_subprocess(run_webui))

    while True:
        try:
            time.sleep(10)
        except KeyboardInterrupt:
            break

    for each in threads:
        each.join()

if __name__ == '__main__':
    if len(sys.argv) < 2:
        all_in_one()
    else:
        cmd = "run_"+sys.argv[1]
        locals()[cmd]()
