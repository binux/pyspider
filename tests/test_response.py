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
        self.httpbin_thread = utils.run_in_subprocess(httpbin.app.run, port=14887, passthrough_errors=False)
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
        result = self.fetcher.fetch(request)
        response = rebuild_response(result)
        return response

    def test_10_html(self):
        response = self.get('/html')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.doc('h1'))

    def test_20_xml(self):
        response = self.get('/xml')
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.doc('item'))

    def test_30_gzip(self):
        response = self.get('/gzip')
        self.assertEqual(response.status_code, 200)
        self.assertIn('gzipped', response.text)

    def test_40_deflate(self):
        response = self.get('/deflate')
        self.assertEqual(response.status_code, 200)
        self.assertIn('deflated', response.text)

    def test_50_ok(self):
        response = self.get('/status/200')
        self.assertTrue(response.ok)
        self.assertTrue(response)
        response = self.get('/status/302')
        self.assertTrue(response.ok)
        self.assertTrue(response)
        with self.assertRaises(Exception):
            self.raise_for_status(allow_redirects=False)

    def test_60_not_ok(self):
        response = self.get('/status/400')
        self.assertFalse(response.ok)
        self.assertFalse(response)
        response = self.get('/status/500')
        self.assertFalse(response.ok)
        self.assertFalse(response)
        response = self.get('/status/600')
        self.assertFalse(response.ok)
        self.assertFalse(response)
