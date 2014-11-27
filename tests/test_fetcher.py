#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-15 22:10:35

import os
import copy
import time
import umsgpack
import xmlrpclib
import subprocess
import unittest2 as unittest
from multiprocessing import Queue

from pyspider.libs import utils
from pyspider.fetcher.tornado_fetcher import Fetcher


class TestFetcher(unittest.TestCase):
    sample_task_http = {
        'taskid': 'taskid',
        'project': 'project',
        'url': 'http://echo.opera.com/',
        'fetch': {
            'method': 'GET',
            'headers': {
                'Cookie': 'a=b',
                'a': 'b'
            },
            'cookies': {
                'c': 'd',
            },
            'timeout': 60,
            'save': 'abc',
        },
        'process': {
            'callback': 'callback',
            'save': [1, 2, 3],
        },
    }

    @classmethod
    def setUpClass(self):
        self.inqueue = Queue(10)
        self.outqueue = Queue(10)
        self.fetcher = Fetcher(self.inqueue, self.outqueue)
        self.fetcher.phantomjs_proxy = 'localhost:25555'
        self.rpc = xmlrpclib.ServerProxy('http://localhost:%d' % 24444)
        self.xmlrpc_thread = utils.run_in_thread(self.fetcher.xmlrpc_run, port=24444)
        self.thread = utils.run_in_thread(self.fetcher.run)
        self.phantomjs = subprocess.Popen(['phantomjs',
            os.path.join(os.path.dirname(__file__),
                '../pyspider/fetcher/phantomjs_fetcher.js'),
            '25555'])

    @classmethod
    def tearDownClass(self):
        self.phantomjs.kill()
        self.phantomjs.wait()
        self.rpc._quit()
        self.thread.join()
        time.sleep(1)

    def test_10_http_get(self):
        result = self.fetcher.sync_fetch(self.sample_task_http)
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['orig_url'], self.sample_task_http['url'])
        self.assertEqual(result['save'], self.sample_task_http['fetch']['save'])
        self.assertIn('content', result)

        content = result['content']
        self.assertIn('<b>A:', content)
        self.assertIn('<b>Cookie:</b>', content)
        self.assertIn('c=d</td>', content)

    def test_10_http_post(self):
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['method'] = 'POST'
        request['fetch']['data'] = 'binux'
        request['fetch']['cookies'] = {'c': 'd'}
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['orig_url'], self.sample_task_http['url'])
        self.assertEqual(result['save'], self.sample_task_http['fetch']['save'])
        self.assertIn('content', result)

        content = result['content']
        self.assertIn('<h2>POST', content)
        self.assertIn('..A:', content)
        self.assertIn('..Cookie:', content)
        # FIXME: cookies in headers not supported
        self.assertNotIn('a=b', content)
        self.assertIn('c=d', content)
        self.assertIn('binux', content)

    def test_20_dataurl_get(self):
        data = copy.deepcopy(self.sample_task_http)
        data['url'] = 'data:,hello'
        result = self.fetcher.sync_fetch(data)
        self.assertEqual(result['status_code'], 200)
        self.assertIn('content', result)
        self.assertEqual(result['content'], 'hello')

    def test_30_with_queue(self):
        data = copy.deepcopy(self.sample_task_http)
        data['url'] = 'data:,hello'
        self.inqueue.put(data)
        task, result = self.outqueue.get()
        self.assertEqual(result['status_code'], 200)
        self.assertIn('content', result)
        self.assertEqual(result['content'], 'hello')

    def test_40_with_rpc(self):
        data = copy.deepcopy(self.sample_task_http)
        data['url'] = 'data:,hello'
        result = umsgpack.unpackb(self.rpc.fetch(data).data)
        self.assertEqual(result['status_code'], 200)
        self.assertIn('content', result)
        self.assertEqual(result['content'], 'hello')

    def test_50_base64_data(self):
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['method'] = 'POST'
        request['fetch']['data'] = "[BASE64-DATA]1tDOxA==[/BASE64-DATA]"
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        self.assertEqual(result['status_code'], 200)
        self.assertIn(' d6 ', result['content'])
        self.assertIn(' d0 ', result['content'])
        self.assertIn(' ce ', result['content'])
        self.assertIn(' c4 ', result['content'])

    def test_60_timeout(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'http://httpbin.org/delay/10'
        request['fetch']['timeout'] = 3
        start_time = time.time()
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        end_time = time.time()
        self.assertGreater(end_time - start_time, 2)
        self.assertLess(end_time - start_time, 4)

    def test_70_phantomjs_url(self):
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['fetch_type'] = 'js'
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['orig_url'], self.sample_task_http['url'])
        self.assertEqual(result['save'], self.sample_task_http['fetch']['save'])
        self.assertIn('content', result)

        content = result['content']
        self.assertIn('<b>a:</b>', content)
        self.assertIn('<b>Cookie:</b>', content)
        self.assertIn('c=d</td>', content)

    def test_80_phantomjs_timeout(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'http://httpbin.org/delay/10'
        request['fetch']['fetch_type'] = 'js'
        request['fetch']['timeout'] = 3
        start_time = time.time()
        result = self.fetcher.sync_fetch(request)
        end_time = time.time()
        self.assertGreater(end_time - start_time, 2)
        self.assertLess(end_time - start_time, 4)

    def test_90_phantomjs_js_script(self):
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['fetch_type'] = 'js'
        request['fetch']['js_script'] = 'function() { document.write("binux") }'
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 200)
        self.assertIn('binux', result['content'])
