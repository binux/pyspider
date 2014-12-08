#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-08 22:23:10

import time

from pyspider.scheduler import Scheduler
from pyspider.fetcher.tornado_fetcher import Fetcher
from pyspider.processor import Processor
from pyspider.result import ResultWorker


class BenchScheduler(Scheduler):
    def __init__(self, *args, **kwargs):
        super(BenchScheduler, self).__init__(*args, **kwargs)
        self.done_cnt = 0
        self.start_time = time.time()
        self.last_report = 0

    def on_task_status(self, task):
        self.done_cnt += 1
        now = time.time()
        if now - self.last_report >= 1:
            self.last_report = now
            rps = self.done_cnt * 1.0 / (now - self.start_time)
            print "Crawled %s pages (at %d pages/min)" % (self.done_cnt, rps*60.0)
        return super(BenchScheduler, self).on_task_status(task)
    

class BenchFetcher(Fetcher):
    def __init__(self, *args, **kwargs):
        super(BenchFetcher, self).__init__(*args, **kwargs)
        self.done_cnt = 0
        self.start_time = time.time()
        self.last_report = 0

    def on_result(self, type, task, result):
        self.done_cnt += 1
        now = time.time()
        if now - self.last_report >= 1:
            self.last_report = now
            rps = self.done_cnt * 1.0 / (now - self.start_time)
            print ("Fetched %s pages (at %d pages/min)" % (self.done_cnt, rps*60.0)).rjust(75)
        return super(BenchFetcher, self).on_result(type, task, result)


class BenchProcessor(Processor):
    def __init__(self, *args, **kwargs):
        super(BenchProcessor, self).__init__(*args, **kwargs)
        self.done_cnt = 0
        self.start_time = time.time()
        self.last_report = 0

    def on_task(self, task, response):
        self.done_cnt += 1
        now = time.time()
        if now - self.last_report >= 1:
            self.last_report = now
            rps = self.done_cnt * 1.0 / (now - self.start_time)
            print " "*75, "Processed %s pages (at %d pages/min)" % (self.done_cnt, rps*60.0)
        return super(BenchProcessor, self).on_task(task, response)


class BenchResultWorker(ResultWorker):
    def __init__(self, *args, **kwargs):
        super(BenchResultWorker, self).__init__(*args, **kwargs)
        self.done_cnt = 0
        self.start_time = time.time()
        self.last_report = 0

    def on_result(self, task, result):
        self.done_cnt += 1
        now = time.time()
        if now - self.last_report >= 1:
            self.last_report = now
            rps = self.done_cnt * 1.0 / (now - self.start_time)
            print ("Saved %s pages (at %d pages/min)" % (self.done_cnt, rps*60.0)).rjust(150)
        super(BenchResultWorker, self).on_result(task, result)


bench_script = '''
from pyspider.libs.base_handler import *

class Handler(BaseHandler):
    def on_start(self):
        self.crawl('http://localhost:5000/bench', params={'total': %(total)d, 'show': %(show)d}, callback=self.index_page)

    def index_page(self, response):
        for each in response.doc('a[href^="http://"]').items():
            self.crawl(each.attr.href, callback=self.index_page)
        return response.url
'''
