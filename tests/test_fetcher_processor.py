#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-01-18 14:09:41

import os
import six
import json
import time
import httpbin
import unittest2 as unittest
try:
    from Queue import Queue
except ImportError:
    from queue import Queue

from pyspider.database.local.projectdb import ProjectDB
from pyspider.fetcher import Fetcher
from pyspider.processor import Processor
from pyspider.libs import utils, dataurl

class TestFetcherProcessor(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.projectdb = ProjectDB([os.path.join(os.path.dirname(__file__), 'data_fetcher_processor_handler.py')])
        self.fetcher = Fetcher(None, None, async=False)
        self.status_queue = Queue()
        self.newtask_queue = Queue()
        self.result_queue = Queue()
        self.httpbin_thread = utils.run_in_subprocess(httpbin.app.run, port=14887)
        self.httpbin = 'http://127.0.0.1:14887'
        self.processor = Processor(projectdb=self.projectdb,
                                   inqueue=None,
                                   status_queue=self.status_queue,
                                   newtask_queue=self.newtask_queue,
                                   result_queue=self.result_queue)
        self.project_name = 'data_fetcher_processor_handler'
        time.sleep(0.5)

    @classmethod
    def tearDownClass(self):
        self.httpbin_thread.terminate()
        self.httpbin_thread.join()

    def crawl(self, url=None, **kwargs):
        if url is None and kwargs.get('callback'):
            url = dataurl.encode(utils.text(kwargs.get('callback')))

        project_data = self.processor.project_manager.get(self.project_name)
        assert project_data, "can't find project: %s" % self.project_name
        instance = project_data['instance']
        instance._reset()
        task = instance.crawl(url, **kwargs)
        assert not isinstance(task, list), 'url list is not allowed'
        task, result = self.fetcher.fetch(task)
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

    def status_ok(self, status, type):
        if not status:
            return False
        return status.get('track', {}).get(type, {}).get('ok', False)

    def assertStatusOk(self, status):
        self.assertTrue(self.status_ok(status, 'fetch'), status.get('track', {}).get('fetch'))
        self.assertTrue(self.status_ok(status, 'process'), status.get('track', {}).get('process'))

    def __getattr__(self, name):
        return name

    def test_10_not_status(self):
        status, newtasks, result = self.crawl(callback=self.not_send_status)

        self.assertIsNone(status)
        self.assertEqual(len(newtasks), 1, newtasks)
        self.assertEqual(result, 'not_send_status')

    def test_20_url_deduplicated(self):
        status, newtasks, result = self.crawl(callback=self.url_deduplicated)

        self.assertStatusOk(status)
        self.assertIsNone(status['track']['fetch']['error'])
        self.assertIsNone(status['track']['fetch']['content'])
        self.assertFalse(status['track']['fetch']['headers'])
        self.assertFalse(status['track']['process']['logs'])
        self.assertEqual(len(newtasks), 2, newtasks)
        self.assertIsNone(result)

    def test_30_catch_status_code_error(self):
        status, newtasks, result = self.crawl(self.httpbin+'/status/418', callback=self.json)

        self.assertFalse(self.status_ok(status, 'fetch'))
        self.assertFalse(self.status_ok(status, 'process'))
        self.assertEqual(status['track']['fetch']['error'], 'HTTP 418: Unknown')
        self.assertTrue(status['track']['fetch']['content'], '')
        self.assertTrue(status['track']['fetch']['headers'])
        self.assertTrue(status['track']['process']['logs'])
        self.assertIn('HTTPError: HTTP 418: Unknown', status['track']['process']['logs'])
        self.assertFalse(newtasks)


        status, newtasks, result = self.crawl(self.httpbin+'/status/400', callback=self.catch_http_error)

        self.assertFalse(self.status_ok(status, 'fetch'))
        self.assertTrue(self.status_ok(status, 'process'))
        self.assertEqual(len(newtasks), 1, newtasks)
        self.assertEqual(result, 400)

        status, newtasks, result = self.crawl(self.httpbin+'/status/500', callback=self.catch_http_error)
        self.assertFalse(self.status_ok(status, 'fetch'))
        self.assertTrue(self.status_ok(status, 'process'))
        self.assertEqual(len(newtasks), 1, newtasks)
        self.assertEqual(result, 500)

        status, newtasks, result = self.crawl(self.httpbin+'/status/302',
                                              allow_redirects=False,
                                              callback=self.catch_http_error)
        self.assertFalse(self.status_ok(status, 'fetch'))
        self.assertTrue(self.status_ok(status, 'process'))
        self.assertEqual(len(newtasks), 1, newtasks)
        self.assertEqual(result, 302)

    def test_40_method(self):
        status, newtasks, result = self.crawl(self.httpbin+'/delete', method='DELETE', callback=self.json)

        self.assertStatusOk(status)
        self.assertFalse(newtasks)

        status, newtasks, result = self.crawl(self.httpbin+'/get', method='PATCH',
                                              callback=self.catch_http_error)

        self.assertFalse(self.status_ok(status, 'fetch'))
        self.assertTrue(self.status_ok(status, 'process'))
        self.assertTrue(newtasks)
        self.assertEqual(result, 405)

    def test_50_params(self):
        status, newtasks, result = self.crawl(self.httpbin+'/get', params={
            'roy': 'binux',
            u'中文': '.',
        }, callback=self.json)

        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertEqual(result['args'], {'roy': 'binux', u'中文': '.'})

    def test_60_data(self):
        status, newtasks, result = self.crawl(self.httpbin+'/post', data={
            'roy': 'binux',
            u'中文': '.',
        }, callback=self.json)

        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertEqual(result['form'], {'roy': 'binux', u'中文': '.'})

    def test_70_redirect(self):
        status, newtasks, result = self.crawl(self.httpbin+'/redirect-to?url=/get', callback=self.json)

        self.assertStatusOk(status)
        self.assertEqual(status['track']['fetch']['redirect_url'], self.httpbin+'/get')
        self.assertFalse(newtasks)

    def test_80_redirect_too_many(self):
        status, newtasks, result = self.crawl(self.httpbin+'/redirect/10', callback=self.json)

        self.assertFalse(self.status_ok(status, 'fetch'))
        self.assertFalse(self.status_ok(status, 'process'))
        self.assertFalse(newtasks)
        self.assertEqual(status['track']['fetch']['status_code'], 599)
        self.assertIn('redirects followed', status['track']['fetch']['error'])

    def test_90_files(self):
        status, newtasks, result = self.crawl(self.httpbin+'/put', method='PUT',
                                              files={os.path.basename(__file__): open(__file__).read()},
                                              callback=self.json)

        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertIn(os.path.basename(__file__), result['files'])

    def test_a100_files_with_data(self):
        status, newtasks, result = self.crawl(self.httpbin+'/put', method='PUT',
                                              files={os.path.basename(__file__): open(__file__).read()},
                                              data={
                                                  'roy': 'binux',
                                                  #'中文': '.', # FIXME: not work
                                              },
                                              callback=self.json)
        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertEqual(result['form'], {'roy': 'binux'})
        self.assertIn(os.path.basename(__file__), result['files'])

    def test_a110_headers(self):
        status, newtasks, result = self.crawl(self.httpbin+'/get',
                                              headers={
                                                  'a': 'b',
                                                  'C-d': 'e-F',
                                              }, callback=self.json)
        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertEqual(result['headers'].get('A'), 'b')
        self.assertEqual(result['headers'].get('C-D'), 'e-F')

    def test_a120_cookies(self):
        status, newtasks, result = self.crawl(self.httpbin+'/get',
                                              cookies={
                                                  'a': 'b',
                                                  'C-d': 'e-F'
                                              }, callback=self.json)
        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertIn('a=b', result['headers'].get('Cookie'))
        self.assertIn('C-d=e-F', result['headers'].get('Cookie'))

    # FIXME: cookies can't use with Cookie header
    #def test_a130_cookies_with_headers(self):
        #status, newtasks, result = self.crawl(self.httpbin+'/get',
                                              #headers={
                                                  #'Cookie': 'g=h; I=j',
                                              #},
                                              #cookies={
                                                  #'a': 'b',
                                                  #'C-d': 'e-F'
                                              #}, callback=self.json)
        #self.assertStatusOk(status)
        #self.assertFalse(newtasks)
        #self.assertEqual(result['headers'].get('Cookie'), 'g=h; I=j; a=b; C-d=e-F')

    def test_a140_response_cookie(self):
        status, newtasks, result = self.crawl(self.httpbin+'/cookies/set?k1=v1&k2=v2',
                                              callback=self.cookies)
        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertEqual(result, {'k1': 'v1', 'k2': 'v2'})

    def test_a150_timeout(self):
        status, newtasks, result = self.crawl(self.httpbin+'/delay/2', timeout=1, callback=self.json)

        self.assertFalse(self.status_ok(status, 'fetch'))
        self.assertFalse(self.status_ok(status, 'process'))
        self.assertFalse(newtasks)
        self.assertEqual(int(status['track']['fetch']['time']), 1)

    def test_a160_etag(self):
        status, newtasks, result = self.crawl(self.httpbin+'/cache', etag='abc', callback=self.json)

        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertFalse(result)

    def test_a170_last_modifed(self):
        status, newtasks, result = self.crawl(self.httpbin+'/cache', last_modifed='0', callback=self.json)

        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertFalse(result)

    def test_a180_save(self):
        status, newtasks, result = self.crawl(callback=self.save, save={'roy': 'binux', u'中文': 'value'})

        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertEqual(result, {'roy': 'binux', u'中文': 'value'})

    def test_a190_taskid(self):
        status, newtasks, result = self.crawl(callback=self.save, taskid='binux-taskid')

        self.assertStatusOk(status)
        self.assertEqual(status['taskid'], 'binux-taskid')
        self.assertFalse(newtasks)
        self.assertFalse(result)

    def test_links(self):
        status, newtasks, result = self.crawl(self.httpbin+'/links/10/0', callback=self.links)

        self.assertStatusOk(status)
        self.assertEqual(len(newtasks), 9, newtasks)
        self.assertFalse(result)

    def test_html(self):
        status, newtasks, result = self.crawl(self.httpbin+'/html', callback=self.html)

        self.assertStatusOk(status)
        self.assertFalse(newtasks)
        self.assertEqual(result, 'Herman Melville - Moby-Dick')
