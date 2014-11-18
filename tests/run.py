#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-18 21:25:16

import os
import sys
import time
import logging
import logging.config
logging.config.fileConfig("logging.conf")
#logging.getLogger('scheduler').setLevel(logging.ERROR)
#logging.getLogger('fetcher').setLevel(logging.ERROR)
#logging.getLogger('processor').setLevel(logging.ERROR)

from multiprocessing import Queue
from pyspider.database import connect_database
from pyspider.libs.utils import Get, run_in_thread

class g(object):
    taskdb = Get(lambda : connect_database('sqlite+taskdb:///data/tests/task.db'))
    projectdb = Get(lambda : connect_database('sqlite+projectdb:///data/tests/project.db'))
    resultdb = Get(lambda : connect_database('sqlite+resultdb:///data/tests/result.db'))
 
    newtask_queue = Queue(100)
    status_queue = Queue(100)
    scheduler2fetcher = Queue(100)
    fetcher2processor = Queue(100)
    processor2result = Queue(100)

def run_scheduler(g=g):
    from pyspider.scheduler import Scheduler
    scheduler = Scheduler(taskdb=g.taskdb, projectdb=g.projectdb, resultdb=g.resultdb,
            newtask_queue=g.newtask_queue, status_queue=g.status_queue,
            out_queue=g.scheduler2fetcher)
    g.scheduler = scheduler
    run_in_thread(scheduler.xmlrpc_run)
    scheduler.run()

def run_fetcher(g=g):
    from pyspider.fetcher.tornado_fetcher import Fetcher
    fetcher = Fetcher(inqueue=g.scheduler2fetcher, outqueue=g.fetcher2processor)
    g.fetcher = fetcher
    run_in_thread(fetcher.xmlrpc_run)
    fetcher.run()

def run_processor(g=g):
    from pyspider.processor import Processor
    processor = Processor(projectdb=g.projectdb,
            inqueue=g.fetcher2processor, status_queue=g.status_queue,
            newtask_queue=g.newtask_queue, result_queue=g.processor2result)
    g.processor = processor
    processor.run()

def run_result_worker(g=g):
    from pyspider.result import ResultWorker
    result_worker = ResultWorker(resultdb=g.resultdb, inqueue=g.processor2result)
    g.result_worker = result_worker
    result_worker.run()

def run_webui(g=g):
    import xmlrpclib
    from pyspider.webui.app import app
    app.config['taskdb'] = g.taskdb
    app.config['projectdb'] = g.projectdb
    app.config['resultdb'] = g.resultdb
    app.config['scheduler_rpc'] = xmlrpclib.ServerProxy('http://localhost:23333')
    g.app = app
    app.run()
