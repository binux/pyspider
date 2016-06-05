#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-15 22:10:35

import os
import json
import copy
import time
import umsgpack
import subprocess
import unittest2 as unittest

import logging
import logging.config
logging.config.fileConfig("pyspider/logging.conf")

try:
    from six.moves import xmlrpc_client
except ImportError:
    import xmlrpclib as xmlrpc_client
from pyspider.libs import utils
from pyspider.libs.multiprocessing_queue import Queue
from pyspider.libs.response import rebuild_response
from pyspider.fetcher.tornado_fetcher import Fetcher


class TestFetcher(unittest.TestCase):
    sample_task_http = {
        'taskid': 'taskid',
        'project': 'project',
        'url': '',
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
        import tests.data_test_webpage
        import httpbin

        self.httpbin_thread = utils.run_in_subprocess(httpbin.app.run, port=14887, passthrough_errors=False)
        self.httpbin = 'http://127.0.0.1:14887'

        self.inqueue = Queue(10)
        self.outqueue = Queue(10)
        self.fetcher = Fetcher(self.inqueue, self.outqueue)
        self.fetcher.phantomjs_proxy = '127.0.0.1:25555'
        self.rpc = xmlrpc_client.ServerProxy('http://localhost:%d' % 24444)
        self.xmlrpc_thread = utils.run_in_thread(self.fetcher.xmlrpc_run, port=24444)
        self.thread = utils.run_in_thread(self.fetcher.run)
        self.proxy_thread = subprocess.Popen(['pyproxy', '--username=binux',
                                              '--password=123456', '--port=14830',
                                              '--debug'], close_fds=True)
        self.proxy = '127.0.0.1:14830'
        try:
            self.phantomjs = subprocess.Popen(['phantomjs',
                os.path.join(os.path.dirname(__file__),
                    '../pyspider/fetcher/phantomjs_fetcher.js'),
                '25555'])
        except OSError:
            self.phantomjs = None
        time.sleep(0.5)

    @classmethod
    def tearDownClass(self):
        self.proxy_thread.terminate()
        self.proxy_thread.wait()
        self.httpbin_thread.terminate()
        self.httpbin_thread.join()

        if self.phantomjs:
            self.phantomjs.kill()
            self.phantomjs.wait()
        self.rpc._quit()
        self.thread.join()

        assert not utils.check_port_open(5000)
        assert not utils.check_port_open(23333)
        assert not utils.check_port_open(24444)
        assert not utils.check_port_open(25555)
        assert not utils.check_port_open(14887)

        time.sleep(1)

    def test_10_http_get(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/get'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(response.orig_url, request['url'])
        self.assertEqual(response.save, request['fetch']['save'])
        self.assertIsNotNone(response.json, response.content)
        self.assertEqual(response.json['headers'].get('A'), 'b', response.json)
        self.assertIn('c=d', response.json['headers'].get('Cookie'), response.json)
        self.assertIn('a=b', response.json['headers'].get('Cookie'), response.json)

    def test_15_http_post(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/post'
        request['fetch']['method'] = 'POST'
        request['fetch']['data'] = 'binux'
        request['fetch']['cookies'] = {'c': 'd'}
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.orig_url, request['url'])
        self.assertEqual(response.save, request['fetch']['save'])
        self.assertIsNotNone(response.json, response.content)

        self.assertEqual(response.json['form'].get('binux'), '')
        self.assertEqual(response.json['headers'].get('A'), 'b', response.json)
        self.assertIn('c=d', response.json['headers'].get('Cookie'), response.json)
        self.assertIn('a=b', response.json['headers'].get('Cookie'), response.json)

    def test_20_dataurl_get(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'data:,hello'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'hello')

    def test_30_with_queue(self):
        request= copy.deepcopy(self.sample_task_http)
        request['url'] = 'data:,hello'
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'hello')

    def test_40_with_rpc(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = 'data:,hello'
        result = umsgpack.unpackb(self.rpc.fetch(request).data)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.text, 'hello')

    def test_50_base64_data(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/post'
        request['fetch']['method'] = 'POST'
        # utf8 encoding 中文
        request['fetch']['data'] = "[BASE64-DATA]5Lit5paH[/BASE64-DATA]"
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, response.error)
        self.assertIsNotNone(response.json, response.content)
        self.assertIn(u'中文', response.json['form'], response.json)

    def test_55_base64_data(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/post'
        request['fetch']['method'] = 'POST'
        # gbk encoding 中文
        request['fetch']['data'] = "[BASE64-DATA]1tDOxA==[/BASE64-DATA]"
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, response.error)
        self.assertIsNotNone(response.json, response.content)

    def test_60_timeout(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/delay/5'
        request['fetch']['timeout'] = 3
        start_time = time.time()
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        end_time = time.time()
        self.assertGreater(end_time - start_time, 1.5)
        self.assertLess(end_time - start_time, 4.5)

        response = rebuild_response(result)
        self.assertEqual(response.orig_url, request['url'])
        self.assertEqual(response.save, request['fetch']['save'])

    def test_65_418(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/status/418'
        self.inqueue.put(request)
        task, result = self.outqueue.get()
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 418)
        self.assertIn('teapot', response.text)

    def test_70_phantomjs_url(self):
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin + '/get'
        request['fetch']['fetch_type'] = 'js'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(response.orig_url, request['url'])
        self.assertEqual(response.save, request['fetch']['save'])
        data = json.loads(response.doc('pre').text())
        self.assertIsNotNone(data, response.content)
        self.assertEqual(data['headers'].get('A'), 'b', response.json)
        self.assertEqual(data['headers'].get('Cookie'), 'c=d', response.json)

    def test_80_phantomjs_timeout(self):
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/delay/5'
        request['fetch']['fetch_type'] = 'js'
        request['fetch']['timeout'] = 3
        start_time = time.time()
        result = self.fetcher.sync_fetch(request)
        end_time = time.time()
        self.assertGreater(end_time - start_time, 2)
        self.assertLess(end_time - start_time, 5)

    def test_90_phantomjs_js_script(self):
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin + '/html'
        request['fetch']['fetch_type'] = 'js'
        request['fetch']['js_script'] = 'function() { document.write("binux") }'
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 200)
        self.assertIn('binux', result['content'])

    def test_a100_phantomjs_sharp_url(self):
        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/pyspider/ajax.html'
        request['fetch']['fetch_type'] = 'js'
        request['fetch']['headers']['User-Agent'] = 'pyspider-test'
        result = self.fetcher.sync_fetch(request)
        self.assertEqual(result['status_code'], 200)
        self.assertNotIn('loading', result['content'])
        self.assertIn('done', result['content'])
        self.assertIn('pyspider-test', result['content'])

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

    def test_a120_http_get_with_proxy_fail(self):
        self.fetcher.proxy = self.proxy
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/get'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 403, result)
        self.fetcher.proxy = None

    def test_a130_http_get_with_proxy_ok(self):
        self.fetcher.proxy = self.proxy
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/get?username=binux&password=123456'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(response.orig_url, request['url'])
        self.assertEqual(response.save, request['fetch']['save'])
        self.assertIsNotNone(response.json, response.content)
        self.assertEqual(response.json['headers'].get('A'), 'b', response.json)
        self.assertIn('c=d', response.json['headers'].get('Cookie'), response.json)
        self.assertIn('a=b', response.json['headers'].get('Cookie'), response.json)
        self.fetcher.proxy = None

    def test_a140_redirect(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/redirect-to?url=/get'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(response.orig_url, request['url'])
        self.assertEqual(response.url, self.httpbin+'/get')

    def test_a150_too_much_redirect(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/redirect/10'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 599, result)
        self.assertIn('redirects followed', response.error)

    def test_a160_cookie(self):
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin+'/cookies/set?k1=v1&k2=v2'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)
        self.assertEqual(response.cookies, {'a': 'b', 'k1': 'v1', 'k2': 'v2', 'c': 'd'}, result)

    def test_a170_validate_cert(self):
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['validate_cert'] = False
        request['url'] = self.httpbin+'/get'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)

    def test_a180_max_redirects(self):
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['max_redirects'] = 10
        request['url'] = self.httpbin+'/redirect/10'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)

    def test_a200_robots_txt(self):
        request = copy.deepcopy(self.sample_task_http)
        request['fetch']['robots_txt'] = False
        request['url'] = self.httpbin+'/deny'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 200, result)

        request['fetch']['robots_txt'] = True
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 403, result)

    def test_zzzz_issue375(self):
        phantomjs_proxy = self.fetcher.phantomjs_proxy
        self.fetcher.phantomjs_proxy = '127.0.0.1:20000'

        if not self.phantomjs:
            raise unittest.SkipTest('no phantomjs')
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = self.httpbin + '/get'
        request['fetch']['fetch_type'] = 'js'
        result = self.fetcher.sync_fetch(request)
        response = rebuild_response(result)

        self.assertEqual(response.status_code, 599, result)

        self.fetcher.phantomjs_proxy = phantomjs_proxy
