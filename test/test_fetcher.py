#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-15 22:10:35

import time
import unittest


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
    def test_http_get(self):
        fetcher = Fetcher(None, None, async=False)
        def callback(type, task, result):
            self.assertEqual(task, self.sample_task_http)
            self.assertEqual(result['status_code'], 200)
            self.assertEqual(result['orig_url'], self.sample_task_http["url"])
            self.assertIn("a=b", result['content'])
        fetcher.fetch(self.sample_task_http, callback=callback)
