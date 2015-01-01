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
import subprocess
import unittest2 as unittest
from multiprocessing import Queue
import logging
import logging.config
logging.config.fileConfig("pyspider/logging.conf")

try:
    from six.moves import xmlrpc_client
except ImportError:
    import xmlrpclib as xmlrpc_client
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
        self.fetcher.phantomjs_proxy = '127.0.0.1:25555'
        self.rpc = xmlrpc_client.ServerProxy('http://localhost:%d' % 24444)
        self.xmlrpc_thread = utils.run_in_thread(self.fetcher.xmlrpc_run, port=24444)
        self.thread = utils.run_in_thread(self.fetcher.run)
        try:
            self.phantomjs = subprocess.Popen(['phantomjs',
                os.path.join(os.path.dirname(__file__),
                    '../pyspider/fetcher/phantomjs_fetcher.js'),
                '25555'])
        except OSError:
            self.phantomjs = None

    @classmethod
    def tearDownClass(self):
        if self.phantomjs:
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
        self.assertIn(b'<b>A:', content)
        self.assertIn(b'<b>Cookie:</b>', content)
        self.assertIn(b'c=d</td>', content)

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
        self.assertIn(b'<h2>POST', content)
        self.assertIn(b'A:', content)
        self.assertIn(b'Cookie:', content)
        # FIXME: cookies in headers not supported
        self.assertNotIn(b'a=b', content)
        self.assertIn(b'c=d', content)
        self.assertIn(b'binux', content)

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
        self.assertIn(b' d6 ', result['content'])
        self.assertIn(b' d0 ', result['content'])
        self.assertIn(b' ce ', result['content'])
        self.assertIn(b' c4 ', result['content'])

    def test_60_timeout(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'http://httpbin.org/delay/10'
        request['fetch']['timeout'] = 3
        start_time = time.time()
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        end_time = time.time()
        self.assertGreater(end_time - start_time, 1.5)
        self.assertLess(end_time - start_time, 4.5)

    def test_65_418(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'http://httpbin.org/status/418'
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        self.assertEqual(result['status_code'], 418)
        self.assertIn(b'teapot', result['content'])

    def test_70_phantomjs_url(self):
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
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
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
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
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['fetch_type'] = 'js'
        request['fetch']['js_script'] = 'function() { document.write("binux") }'
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 200)
        self.assertIn('binux', result['content'])

    @unittest.skipIf(os.environ.get('IGNORE_GOOGLE'), "can't connect to google.")
    def test_a100_phantomjs_sharp_url(self):
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'https://groups.google.com/forum/#!forum/pyspider-users'
        request['fetch']['fetch_type'] = 'js'
        request['fetch']['headers']['User-Agent'] = 'Mozilla/5.0'
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 200)
        self.assertIn('pyspider-users', result['content'])

    def test_a110_dns_error(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'http://www.not-exists-site.com/'
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 599)
        self.assertIn('error', result)
        self.assertIn('resolve', result['error'])

        self.inqueue.put(request)
        task, result = self.outqueue.get()
        self.assertEqual(result['status_code'], 599)
        self.assertIn('error', result)
        self.assertIn('resolve', result['error'])
