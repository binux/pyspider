#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-01-18 11:10:27


import os
import copy
import time
import httpbin
import unittest2 as unittest

import logging
import logging.config
logging.config.fileConfig("pyspider/logging.conf")

from pyspider.libs import utils
from pyspider.libs.response import rebuild_response
from pyspider.fetcher.tornado_fetcher import Fetcher

class TestResponse(unittest.TestCase):
    sample_task_http = {
        'taskid': 'taskid',
        'project': 'project',
        'url': '',
    }

    @classmethod
    def setUpClass(self):
        self.fetcher = Fetcher(None, None, async=False)
        self.httpbin_thread = utils.run_in_subprocess(httpbin.app.run, port=14887)
        self.httpbin = 'http://127.0.0.1:14887'
        time.sleep(0.5)

    @classmethod
    def tearDownClass(self):
        self.httpbin_thread.terminate()

    def get(self, url, **kwargs):
        if not url.startswith('http://'):
            url = self.httpbin + url
        request = copy.deepcopy(self.sample_task_http)
        request['url'] = url
        request.update(kwargs)
        task, result = self.fetcher.fetch(request)
        response = rebuild_response(result)
        self.assertEqual(response.status_code, 200, result)
        return response

    def test_10_html(self):
        response = self.get('/html')
        self.assertIsNotNone(response.doc('h1'))

    def test_20_xml(self):
        response = self.get('/xml')
        self.assertIsNotNone(response.doc('item'))

    def test_30_gzip(self):
        response = self.get('/gzip')
        self.assertIn('gzipped', response.text)

    def test_40_deflate(self):
        response = self.get('/deflate')
        self.assertIn('deflated', response.text)
