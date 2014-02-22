#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 14:00:05

import os
import time
import unittest

from processor import project_module
class TestProjectModule(unittest.TestCase):
    base_task = {
            'taskid': 'taskid',
            'project': 'test.project',
            'url': 'www.baidu.com/',
            'schedule': {
                'priority': 1,
                'retries': 3,
                'exetime': 0,
                'age': 3600,
                'itag': 'itag',
                'recrawl': 5,
                },
            'fetch': {
                'method': 'GET',
                'headers': {
                    'Cookie': 'a=b', 
                    },
                'data': 'a=b&c=d', 
                'timeout': 60,
                },
            'process': {
                'callback': 'callback',
                'save': [1, 2, 3],
                },
            }
    fetch_result = {
            'status_code': 200,
            'orig_url': 'www.baidu.com/',
            'url': 'http://www.baidu.com/',
            'headers': {
                'cookie': 'abc',
                },
            'content': 'test data',
            'cookies': {
                'a': 'b',
                },
            }

    def setUp(self):
        self.project = "test.project"
        self.script = open(os.path.join(os.path.dirname(__file__), 'data_handler.py')).read()
        self.env = {
                'test': True,
                }
        self.project_info = {
                'name': self.project,
                'status': 'DEBUG',
                }

    def test_build_module(self):
        module = project_module.ProjectModule(self.project, self.script, self.env)
        module.rethrow()
        _class = module.get()
        instance = _class()._init(self.project_info)

        # hello
        self.base_task['process']['callback'] = 'hello'
        ret = instance.run(module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, "hello world!")

        # echo
        self.base_task['process']['callback'] = 'echo'
        ret = instance.run(module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, "test data")

        # saved
        self.base_task['process']['callback'] = 'saved'
        ret = instance.run(module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, self.base_task['process']['save'])

        # echo task
        self.base_task['process']['callback'] = 'echo_task'
        ret = instance.run(module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, self.project)

        # catch_status_code
        self.fetch_result['status_code'] = 403
        self.base_task['process']['callback'] = 'catch_status_code'
        ret = instance.run(module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, 403)
        self.fetch_result['status_code'] = 200

        # raise_exception 
        self.base_task['process']['callback'] = 'raise_exception'
        ret = instance.run(module, self.base_task, self.fetch_result)
        self.assertIsNotNone(ret.exception)
        logstr = ret.logstr()
        self.assertIn('info', logstr)
        self.assertIn('warning', logstr)
        self.assertIn('error', logstr)

        # echo
        self.base_task['process']['callback'] = 'add_task'
        ret = instance.run(module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(len(ret.follows), 1)
        self.assertEqual(len(ret.messages), 1)
