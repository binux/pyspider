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

# config form environment -------------------

scheduler_xmlrpc_port = int(os.environ.get('SCHEDULER_XMLRPC_PORT', 23333))
fetcher_xmlrpc_port = int(os.environ.get('FETCHER_XMLRPC_PORT', 24444))
webui_host = os.environ.get('WEBUI_HOST', '0.0.0.0')
webui_port = int(os.environ.get('WEBUI_PORT', 5000))
debug = bool(os.environ.get('DEBUG'))
queue_maxsize = int(os.environ.get('QUEUE_MAXSIZE', 100))

def get_taskdb():
    if os.environ.get('MYSQL_NAME'):
        return connect_database('mysql+taskdb://%(MYSQL_PORT_3306_TCP_ADDR)s:%(MYSQL_PORT_3306_TCP_PORT)s/pyspider' % os.environ)
    elif os.environ.get('TASKDB'):
        return connect_database(os.environ['TAKDB'])
    else:
        return connect_database('sqlite+taskdb:///data/task.db')

def get_projectdb():
    if os.environ.get('DB_NAME'):
        return connect_database('mysql+projectdb://%(MYSQL_PORT_3306_TCP_ADDR)s:%(MYSQL_PORT_3306_TCP_PORT)s/pyspider' % os.environ)
    elif os.environ.get('PROJECTDB'):
        return connect_database(os.environ['PROJECTDB'])
    else:
        return connect_database('sqlite+projectdb:///data/project.db')

if os.environ.get('RABBITMQ_NAME'):
    from libs.rabbitmq import Queue
    amqp_url = 'amqp://guest:guest@%(RABBITMQ_PORT_5672_TCP_ADDR)s:%(RABBITMQ_PORT_5672_TCP_PORT)s/%2F' % os.environ
    newtask_queue = Queue("newtask_queue", amqp_url=amqp_url, maxsize=queue_maxsize)
    status_queue = Queue("status_queue", amqp_url=amqp_url, maxsize=queue_maxsize)
    scheduler2fetcher = Queue("scheduler2fetcher", amqp_url=amqp_url, maxsize=queue_maxsize)
    fetcher2processor = Queue("fetcher2processor", amqp_url=amqp_url, maxsize=queue_maxsize)
else:
    from multiprocessing import Queue
    newtask_queue = Queue(queue_maxsize)
    status_queue = Queue(queue_maxsize)
    scheduler2fetcher = Queue(queue_maxsize)
    fetcher2processor = Queue(queue_maxsize)

# run commands ------------------------------------------
def run_scheduler():
    from scheduler import Scheduler
    scheduler = Scheduler(taskdb=get_taskdb(), projectdb=get_projectdb(),
            newtask_queue=newtask_queue, status_queue=status_queue, out_queue=scheduler2fetcher)

    run_in_thread(scheduler.xmlrpc_run, port=scheduler_xmlrpc_port, bind=webui_host)
    scheduler.run()

def run_fetcher():
    from fetcher.tornado_fetcher import Fetcher
    fetcher = Fetcher(inqueue=scheduler2fetcher, outqueue=fetcher2processor)

    run_in_thread(fetcher.xmlrpc_run, port=fetcher_xmlrpc_port, bind=webui_host)
    fetcher.run()

def run_processor():
    from processor import Processor
    processor = Processor(projectdb=get_projectdb(),
            inqueue=fetcher2processor, status_queue=status_queue, newtask_queue=newtask_queue)
    
    processor.run()

scheduler_rpc = None
if os.environ.get('SCHEDULER_NAME'):
    import xmlrpclib
    scheduler_rpc = xmlrpclib.ServerProxy('http://%s:%d' % \
            os.environ['SCHEDULER_PORT_%d_TCP_ADDR' % scheduler_xmlrpc_port],
            os.environ['SCHEDULER_PORT_%d_TCP_PORT' % scheduler_xmlrpc_port])

def run_webui():
    import cPickle as pickle

    from webui.app import app
    app.config['taskdb'] = get_taskdb()
    app.config['projectdb'] = get_projectdb()
    app.config['scheduler_rpc'] = scheduler_rpc
    #app.config['cdn'] = '//cdnjs.cloudflare.com/ajax/libs/'
    app.run(host=webui_host, port=webui_port)

def all_in_one():
    import xmlrpclib
    global scheduler_rpc
    scheduler_rpc = xmlrpclib.ServerProxy('http://localhost:%d' % \
            scheduler_xmlrpc_port)

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
