#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-01-18 14:09:41

import os
import time
import httpbin
import subprocess
import unittest

from pyspider.database.local.projectdb import ProjectDB
from pyspider.fetcher import Fetcher
from pyspider.processor import Processor
from pyspider.libs import utils, dataurl
from six.moves.queue import Queue


class TestFetcherProcessor(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.projectdb = ProjectDB([os.path.join(os.path.dirname(__file__), 'data_fetcher_processor_handler.py')])
        self.fetcher = Fetcher(None, None, async_mode=False)
        self.status_queue = Queue()
        self.newtask_queue = Queue()
        self.result_queue = Queue()
        self.httpbin_thread = utils.run_in_subprocess(httpbin.app.run, port=14887, passthrough_errors=False)
        self.httpbin = 'http://127.0.0.1:14887'
        self.proxy_thread = subprocess.Popen(['pyproxy', '--username=binux',
                                              '--password=123456', '--port=14830',
                                              '--debug'], close_fds=True)
        self.proxy = '127.0.0.1:14830'
        self.processor = Processor(projectdb=self.projectdb,
                                   inqueue=None,
                                   status_queue=self.status_queue,
                                   newtask_queue=self.newtask_queue,
                                   result_queue=self.result_queue)
        self.project_name = 'data_fetcher_processor_handler'
        time.sleep(0.5)

    @classmethod
    def tearDownClass(self):
        self.proxy_thread.terminate()
        self.proxy_thread.wait()
        self.httpbin_thread.terminate()
        self.httpbin_thread.join()

    @classmethod
    def crawl(self, url=None, track=None, **kwargs):
        if url is None and kwargs.get('callback'):
            url = dataurl.encode(utils.text(kwargs.get('callback')))

        project_data = self.processor.project_manager.get(self.project_name)
        assert project_data, "can't find project: %s" % self.project_name
        instance = project_data['instance']
        instance._reset()
        task = instance.crawl(url, **kwargs)
        if isinstance(task, list):
            task = task[0]
        task['track'] = track
        result = self.fetcher.fetch(task)
        self.processor.on_task(task, result)

        status = None
        while not self.status_queue.empty():
            status = self.status_queue.get()
        newtasks = []
        while not self.newtask_queue.empty():
            newtasks = self.newtask_queue.get()
        result = None
        while not self.result_queue.empty():
            _, result = self.result_queue.get()
        return status, newtasks, result

    @classmethod
    def status_ok(self, status, type):
        if not status:
            return False
        return status.get('track', {}).get(type, {}).get('ok', False)

    @classmethod
    def assertStatusOk(self, status):
        self.assertTrue(self.status_ok(status, 'fetch'), status.get('track', {}).get('fetch'))
        self.assertTrue(self.status_ok(status, 'process'), status.get('track', {}).get('process'))

    @classmethod
    def __getattr__(self, name):
        return name

    def test_999_true(self):
        self.assertIsNone(None)