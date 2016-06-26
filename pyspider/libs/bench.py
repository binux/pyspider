#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-08 22:23:10

import time
import logging
logger = logging.getLogger('bench')

from six.moves import queue as Queue
from pyspider.scheduler import ThreadBaseScheduler as Scheduler
from pyspider.fetcher.tornado_fetcher import Fetcher
from pyspider.processor import Processor
from pyspider.result import ResultWorker
from pyspider.libs.utils import md5string


def bench_test_taskdb(taskdb):
    project_name = '__bench_test__'
    task = {
        "fetch": {
            "fetch_type": "js",
            "headers": {
                "User-Agent": "BaiDuSpider"
            }
        },
        "process": {
            "callback": "detail_page"
        },
        "project": project_name,
        "taskid": "553300d2582154413b4982c00c34a2d5",
        "url": "http://www.sciencedirect.com/science/article/pii/S1674200109000704"
    }

    track = {
        "fetch": {
            "content": None,
            "encoding": "unicode",
            "error": None,
            "headers": {
                "last-modified": "Wed, 04 Mar 2015 09:24:33 GMT"
            },
            "ok": True,
            "redirect_url": None,
            "status_code": 200,
            "time": 5.543
        },
        "process": {
            "exception": None,
            "follows": 4,
            "logs": "",
            "ok": True,
            "result": "{'url': u'",
            "time": 0.07105398178100586
        }
    }

    def test_insert(n, start=0):
        logger.info("taskdb insert %d", n)
        start_time = time.time()
        for i in range(n):
            task['url'] = 'http://bench.pyspider.org/?l=%d' % (i + start)
            task['taskid'] = md5string(task['url'])
            task['track'] = {}
            taskdb.insert(task['project'], task['taskid'], task)
        end_time = time.time()
        cost_time = end_time - start_time
        logger.info("cost %.2fs, %.2f/s %.2fms",
                    cost_time, n * 1.0 / cost_time, cost_time / n * 1000)

    def test_update(n, start=0):
        logger.info("taskdb update %d" % n)
        start_time = time.time()
        for i in range(n):
            task['url'] = 'http://bench.pyspider.org/?l=%d' % (i + start)
            task['taskid'] = md5string(task['url'])
            task['track'] = track
            taskdb.update(task['project'], task['taskid'], task)
        end_time = time.time()
        cost_time = end_time - start_time
        logger.info("cost %.2fs, %.2f/s %.2fms",
                    cost_time, n * 1.0 / cost_time, cost_time / n * 1000)

    request_task_fields = [
        'taskid',
        'project',
        'url',
        'status',
        'fetch',
        'process',
        'track',
        'lastcrawltime'
    ]

    def test_get(n, start=0, random=True, fields=request_task_fields):
        logger.info("taskdb get %d %s" % (n, "randomly" if random else ""))
        range_n = list(range(n))
        if random:
            from random import shuffle
            shuffle(range_n)
        start_time = time.time()
        for i in range_n:
            task['url'] = 'http://bench.pyspider.org/?l=%d' % (i + start)
            task['taskid'] = md5string(task['url'])
            task['track'] = track
            taskdb.get_task(task['project'], task['taskid'], fields=fields)
        end_time = time.time()
        cost_time = end_time - start_time
        logger.info("cost %.2fs, %.2f/s %.2fms",
                    cost_time, n * 1.0 / cost_time, cost_time / n * 1000)

    try:
        test_insert(1000)
        test_update(1000)
        test_get(1000)
        test_insert(10000, 1000)
        test_update(10000, 1000)
        test_get(10000, 1000)
    except Exception as e:
        logger.exception(e)
    finally:
        taskdb.drop(project_name)


def bench_test_message_queue(queue):
    task = {
        "fetch": {
            "fetch_type": "js",
            "headers": {
                "User-Agent": "BaiDuSpider"
            }
        },
        "process": {
            "callback": "detail_page"
        },
        "project": "__bench_test__",
        "taskid": "553300d2582154413b4982c00c34a2d5",
        "url": "http://www.sciencedirect.com/science/article/pii/S1674200109000704"
    }

    def test_put(n):
        logger.info("message queue put %d", n)
        start_time = time.time()
        for i in range(n):
            task['url'] = 'http://bench.pyspider.org/?l=%d' % i
            task['taskid'] = md5string(task['url'])
            queue.put(task, block=True, timeout=1)
        end_time = time.time()
        cost_time = end_time - start_time
        logger.info("cost %.2fs, %.2f/s %.2fms",
                    cost_time, n * 1.0 / cost_time, cost_time / n * 1000)

    def test_get(n):
        logger.info("message queue get %d", n)
        start_time = time.time()
        for i in range(n):
            try:
                queue.get(True, 1)
            except Queue.Empty:
                logger.error('message queue empty while get %d', i)
                raise
        end_time = time.time()
        cost_time = end_time - start_time
        logger.info("cost %.2fs, %.2f/s %.2fms",
                    cost_time, n * 1.0 / cost_time, cost_time / n * 1000)

    try:
        test_put(1000)
        test_get(1000)
        test_put(10000)
        test_get(10000)
    except Exception as e:
        logger.exception(e)
    finally:
        if hasattr(queue, 'channel'):
            queue.channel.queue_purge(queue.name)

        # clear message queue
        try:
            while queue.get(False):
                continue
        except Queue.Empty:
            pass


class BenchMixin(object):
    """Report to logger for bench test"""
    def _bench_init(self):
        self.done_cnt = 0
        self.start_time = time.time()
        self.last_cnt = 0
        self.last_report = 0

    def _bench_report(self, name, prefix=0, rjust=0):
        self.done_cnt += 1
        now = time.time()
        if now - self.last_report >= 1:
            rps = float(self.done_cnt - self.last_cnt) / (now - self.last_report)
            output = ''
            if prefix:
                output += " " * prefix
            output += ("%s %s pages (at %d pages/min)" % (
                name, self.done_cnt, rps * 60.0)).rjust(rjust)
            logger.info(output)
            self.last_cnt = self.done_cnt
            self.last_report = now


class BenchScheduler(Scheduler, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchScheduler, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_task_status(self, task):
        self._bench_report('Crawled')
        return super(BenchScheduler, self).on_task_status(task)


class BenchFetcher(Fetcher, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchFetcher, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_result(self, type, task, result):
        self._bench_report("Fetched", 0, 75)
        return super(BenchFetcher, self).on_result(type, task, result)


class BenchProcessor(Processor, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchProcessor, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_task(self, task, response):
        self._bench_report("Processed", 75)
        return super(BenchProcessor, self).on_task(task, response)


class BenchResultWorker(ResultWorker, BenchMixin):
    def __init__(self, *args, **kwargs):
        super(BenchResultWorker, self).__init__(*args, **kwargs)
        self._bench_init()

    def on_result(self, task, result):
        self._bench_report("Saved", 0, 150)
        super(BenchResultWorker, self).on_result(task, result)


bench_script = '''
from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    def on_start(self):
        self.crawl('http://127.0.0.1:5000/bench',
                   params={'total': %(total)d, 'show': %(show)d},
                   callback=self.index_page)

    def index_page(self, response):
        for each in response.doc('a[href^="http://"]').items():
            self.crawl(each.attr.href, callback=self.index_page)
        return response.url
'''
