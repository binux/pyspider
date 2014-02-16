#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-15 22:10:35

import time
import threading
import unittest


import json
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
                'data': 'a=b&c=d', 
                'timeout': 60,
                },
            'process': {
                'callback': 'callback',
                'save': [1, 2, 3],
                },
            }
    def setUp(self):
        self.fetcher = Fetcher(None, None)
        self.thread = threading.Thread(target=self.fetcher.run)
        self.thread.daemon = True
        self.thread.start()

    def tearDown(self):
        self.fetcher.quit()
        self.thread.join()

    def test_http_get(self):
        result = self.fetcher.sync_fetch(self.sample_task_http)
        self.assertEqual(result['status_code'], 200)
        self.assertEqual(result['orig_url'], self.sample_task_http['url'])
        self.assertIn('content', result)
        content = json.loads(result['content'])
        self.assertIn('headers', content)
        self.assertIn('A', content['headers'])
        self.assertIn('Cookie', content['headers'])
        self.assertEqual(content['headers']['Cookie'], 'a=b')
