#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-15 22:10:35

import time
import json
import logging
import unittest

from libs import utils
from fetcher.tornado_fetcher import Fetcher

class TestTaskDB(unittest.TestCase):
    sample_task_http = {
            'taskid': 'taskid',
            'project': 'project',
            'url': 'http://httpbin.org/get',
            'fetch': {
                'method': 'GET',
                'headers': {
                    'Cookie': 'a=b', 
                    'a': 'b'
                    },
                'timeout': 60,
                'save': 'abc',
                },
            'process': {
                'callback': 'callback',
                'save': [1, 2, 3],
                },
            }
    def setUp(self):
        self.fetcher = Fetcher(None, None)
        self.thread = utils.run_in_thread(self.fetcher.run)

    def tearDown(self):
        self.fetcher.quit()
        self.thread.join()

    def test_http_get(self):
        result = self.fetcher.sync_fetch(self.sample_task_http)
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['orig_url'], self.sample_task_http['url'])
        self.assertEqual(result['save'], self.sample_task_http['fetch']['save'])
        self.assertIn('content', result)

        content = json.loads(result['content'])
        self.assertIn('headers', content)
        self.assertIn('A', content['headers'])
        self.assertIn('Cookie', content['headers'])
        self.assertEqual(content['headers']['Cookie'], 'a=b')

    def test_dataurl_get(self):
        data = dict(self.sample_task_http)
        data['url'] = 'data:,hello';
        result = self.fetcher.sync_fetch(data)
        self.assertEqual(result['status_code'], 200)
        self.assertIn('content', result)
        self.assertEqual(result['content'], 'hello')
