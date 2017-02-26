#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2017-02-26 10:35:23

import unittest2 as unittest

from pyspider.libs.base_handler import BaseHandler


class TestBaseHandler(unittest.TestCase):
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

    def test_task_join_crawl_config(self):
        task = dict(self.sample_task_http)
        crawl_config = {
            'taskid': 'xxxx',       # should not affect finial task
            'proxy': 'username:password@hostname:port',  # should add proxy
            'headers': {            # should merge headers
                'Cookie': 'abc',    # should not affect cookie
                'c': 'd',           # should add header c
            }
        }
        
        ret = BaseHandler.task_join_crawl_config(task, crawl_config)
        self.assertDictEqual(ret, {
            'taskid': 'taskid',
            'project': 'project',
            'url': '',
            'fetch': {
                'method': 'GET',
                'proxy': 'username:password@hostname:port',
                'headers': {
                    'Cookie': 'a=b',
                    'a': 'b',
                    'c': 'd'
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
        });
