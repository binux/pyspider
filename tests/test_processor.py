#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 14:00:05

import os
import six
import copy
import time
import unittest2 as unittest
import logging.config
logging.config.fileConfig("pyspider/logging.conf")

from pyspider.libs import utils
from pyspider.processor.project_module import ProjectManager


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
            'save': [1, 2, 3],
        },
        'process': {
            'callback': 'callback',
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
        'save': [1, 2, 3],
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
        data = ProjectManager.build_module({
            'name': self.project,
            'script': self.script
        }, {'test': True})
        self.module = data['module']
        self.instance = data['instance']

    def test_2_hello(self):
        self.base_task['process']['callback'] = 'hello'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, "hello world!")

    def test_3_echo(self):
        self.base_task['process']['callback'] = 'echo'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, "test data")

    def test_4_saved(self):
        self.base_task['process']['callback'] = 'saved'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, self.base_task['fetch']['save'])

    def test_5_echo_task(self):
        self.base_task['process']['callback'] = 'echo_task'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, self.project)

    def test_6_catch_status_code(self):
        self.fetch_result['status_code'] = 403
        self.base_task['process']['callback'] = 'catch_status_code'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertEqual(ret.result, 403)
        self.fetch_result['status_code'] = 200

    def test_7_raise_exception(self):
        self.base_task['process']['callback'] = 'raise_exception'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNotNone(ret.exception)
        logstr = ret.logstr()
        self.assertIn('info', logstr)
        self.assertIn('warning', logstr)
        self.assertIn('error', logstr)

    def test_8_add_task(self):
        self.base_task['process']['callback'] = 'add_task'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception, ret.logstr())
        self.assertEqual(len(ret.follows), 1)
        self.assertEqual(len(ret.messages), 1)

    def test_10_cronjob(self):
        task = {
            'taskid': '_on_cronjob',
            'project': self.project,
            'url': 'data:,_on_cronjob',
            'fetch': {
                'save': {
                    'tick': 11,
                },
            },
            'process': {
                'callback': '_on_cronjob',
            },
        }
        fetch_result = copy.deepcopy(self.fetch_result)
        fetch_result['save'] = {
            'tick': 11,
        }
        ret = self.instance.run_task(self.module, task, fetch_result)
        logstr = ret.logstr()
        self.assertNotIn('on_cronjob1', logstr)
        self.assertNotIn('on_cronjob2', logstr)

        task['fetch']['save']['tick'] = 10
        fetch_result['save'] = task['fetch']['save']
        ret = self.instance.run_task(self.module, task, fetch_result)
        logstr = ret.logstr()
        self.assertNotIn('on_cronjob1', logstr)
        self.assertIn('on_cronjob2', logstr)

        task['fetch']['save']['tick'] = 60
        fetch_result['save'] = task['fetch']['save']
        ret = self.instance.run_task(self.module, task, fetch_result)
        logstr = ret.logstr()
        self.assertIn('on_cronjob1', logstr)
        self.assertIn('on_cronjob2', logstr)

    def test_20_get_info(self):
        task = {
            'taskid': '_on_get_info',
            'project': self.project,
            'url': 'data:,_on_get_info',
            'fetch': {
                'save': ['min_tick', 'retry_delay'],
            },
            'process': {
                'callback': '_on_get_info',
            },
        }
        fetch_result = copy.deepcopy(self.fetch_result)
        fetch_result['save'] = task['fetch']['save']

        ret = self.instance.run_task(self.module, task, fetch_result)
        self.assertEqual(len(ret.save), 2, ret.logstr())
        for each in ret.follows:
            self.assertEqual(each['url'], 'data:,on_get_info')
            self.assertEqual(each['fetch']['save']['min_tick'], 10)
            self.assertEqual(each['fetch']['save']['retry_delay'], {})

    def test_30_generator(self):
        self.base_task['process']['callback'] = 'generator'
        ret = self.instance.run_task(self.module, self.base_task, self.fetch_result)
        self.assertIsNone(ret.exception)
        self.assertIn('generator object', repr(ret.result))

import shutil
import inspect
from pyspider.database.sqlite import projectdb
from pyspider.processor.processor import Processor
from pyspider.libs.multiprocessing_queue import Queue
from pyspider.libs.utils import run_in_thread
from pyspider.libs import sample_handler


class TestProcessor(unittest.TestCase):
    projectdb_path = './data/tests/project.db'

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/tests/', ignore_errors=True)
        os.makedirs('./data/tests/')

        def get_projectdb():
            return projectdb.ProjectDB(self.projectdb_path)
        self.projectdb = get_projectdb()
        self.in_queue = Queue(10)
        self.status_queue = Queue(10)
        self.newtask_queue = Queue(10)
        self.result_queue = Queue(10)

        def run_processor():
            self.processor = Processor(get_projectdb(), self.in_queue,
                                       self.status_queue, self.newtask_queue, self.result_queue)
            self.processor.project_manager.CHECK_PROJECTS_INTERVAL = 0.1
            self.processor.run()
        self.process = run_in_thread(run_processor)
        time.sleep(1)

    @classmethod
    def tearDownClass(self):
        if self.process.is_alive():
            self.processor.quit()
            self.process.join(2)
        assert not self.process.is_alive()
        shutil.rmtree('./data/tests/', ignore_errors=True)

    def test_10_update_project(self):
        self.assertIsNone(self.processor.project_manager.get('test_project'))
        self.projectdb.insert('test_project', {
            'name': 'test_project',
            'group': 'group',
            'status': 'TODO',
            'script': inspect.getsource(sample_handler),
            'comments': 'test project',
            'rate': 1.0,
            'burst': 10,
        })
        self.assertIsNone(self.processor.project_manager.get('not_exists'))
        self.assertIsNotNone(self.processor.project_manager.get('test_project'))

        task = {
            "process": {
                "callback": "on_start"
            },
            "project": "not_exists",
            "taskid": "data:,on_start",
            "url": "data:,on_start"
        }
        self.in_queue.put((task, {}))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        while not self.status_queue.empty():
            status = self.status_queue.get()
        self.assertEqual(status['track']['process']['ok'], False)
        self.assertIsNone(self.processor.project_manager.get('not_exists'))

    def test_20_broken_project(self):
        self.assertIsNone(self.processor.project_manager.get('test_broken_project'))
        self.projectdb.insert('test_broken_project', {
            'name': 'test_broken_project',
            'group': 'group',
            'status': 'DEBUG',
            'script': inspect.getsource(sample_handler)[:10],
            'comments': 'test project',
            'rate': 1.0,
            'burst': 10,
        })
        self.assertIsNone(self.processor.project_manager.get('not_exists'))
        self.assertIsNotNone(self.processor.project_manager.get('test_broken_project'))
        project_data = self.processor.project_manager.get('test_broken_project')
        self.assertIsNotNone(project_data.get('exception'))

    def test_30_new_task(self):
        self.assertTrue(self.status_queue.empty())
        self.assertTrue(self.newtask_queue.empty())
        task = {
            "process": {
                "callback": "on_start"
            },
            "project": "test_project",
            "taskid": "data:,on_start",
            "url": "data:,on_start"
        }
        fetch_result = {
            "orig_url": "data:,on_start",
            "content": "on_start",
            "headers": {},
            "status_code": 200,
            "url": "data:,on_start",
            "time": 0,
        }
        self.in_queue.put((task, fetch_result))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        while not self.status_queue.empty():
            self.status_queue.get()
        self.assertFalse(self.newtask_queue.empty())

    def test_40_index_page(self):
        task = None
        while not self.newtask_queue.empty():
            task = self.newtask_queue.get()[0]
        self.assertIsNotNone(task)

        fetch_result = {
            "orig_url": task['url'],
            "content": (
                "<html><body>"
                "<a href='http://binux.me'>binux</a>"
                "<a href='http://binux.me/中文'>binux</a>"
                "<a href='http://binux.me/1'>1</a>"
                "<a href='http://binux.me/1'>2</a>"
                "</body></html>"
            ),
            "headers": {'a': 'b', 'etag': 'tag'},
            "status_code": 200,
            "url": task['url'],
            "time": 0,
        }
        self.in_queue.put((task, fetch_result))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        self.assertFalse(self.newtask_queue.empty())

        status = self.status_queue.get()
        self.assertEqual(status['track']['fetch']['ok'], True)
        self.assertEqual(status['track']['fetch']['time'], 0)
        self.assertEqual(status['track']['fetch']['status_code'], 200)
        self.assertEqual('tag', status['track']['fetch']['headers']['etag'])
        self.assertIsNone(status['track']['fetch']['content'])
        self.assertEqual(status['track']['process']['ok'], True)
        self.assertGreater(status['track']['process']['time'], 0)
        self.assertEqual(status['track']['process']['follows'], 3)
        self.assertIsNone(status['track']['process']['result'])
        self.assertEqual(status['track']['process']['logs'], '')
        self.assertIsNone(status['track']['process']['exception'])

        tasks = self.newtask_queue.get()
        self.assertEqual(len(tasks), 3)
        self.assertEqual(tasks[0]['url'], 'http://binux.me/')
        self.assertTrue(tasks[1]['url'].startswith('http://binux.me/%'), task['url'])

    def test_50_fetch_error(self):
        # clear new task queue
        while not self.newtask_queue.empty():
            self.newtask_queue.get()
        # clear status queue
        while not self.status_queue.empty():
            self.status_queue.get()

        task = {
            "process": {
                "callback": "index_page"
            },
            "project": "test_project",
            "taskid": "data:,test_fetch_error",
            "url": "data:,test_fetch_error"
        }

        fetch_result = {
            "orig_url": task['url'],
            "content": "test_fetch_error",
            "error": "test_fetch_error",
            "headers": {'a': 'b', 'last-modified': '123'},
            "status_code": 598,
            "url": task['url'],
            "time": 0,
        }

        self.in_queue.put((task, fetch_result))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        self.assertTrue(self.newtask_queue.empty())

        status = self.status_queue.get()
        self.assertEqual(status['track']['fetch']['ok'], False)
        self.assertEqual(status['track']['fetch']['time'], 0)
        self.assertEqual(status['track']['fetch']['status_code'], 598)
        self.assertEqual('123', status['track']['fetch']['headers']['last-modified'])
        self.assertIsNotNone(status['track']['fetch']['content'])
        self.assertEqual(status['track']['process']['ok'], False)
        self.assertGreater(status['track']['process']['time'], 0)
        self.assertEqual(status['track']['process']['follows'], 0)
        self.assertIsNone(status['track']['process']['result'])
        self.assertGreater(len(status['track']['process']['logs']), 0)
        self.assertIsNotNone(status['track']['process']['exception'])

    def test_60_call_broken_project(self):
        # clear new task queue
        while not self.newtask_queue.empty():
            self.newtask_queue.get()
        # clear status queue
        while not self.status_queue.empty():
            self.status_queue.get()

        task = {
            "process": {
                "callback": "on_start"
            },
            "project": "test_broken_project",
            "taskid": "data:,on_start",
            "url": "data:,on_start",
        }
        fetch_result = {
            "orig_url": "data:,on_start",
            "content": "on_start",
            "headers": {},
            "status_code": 200,
            "url": "data:,on_start",
            "time": 0,
        }
        self.in_queue.put((task, fetch_result))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        while not self.status_queue.empty():
            status = self.status_queue.get()
        self.assertEqual(status['track']['fetch']['ok'], True)
        self.assertEqual(status['track']['process']['ok'], False)
        self.assertGreater(len(status['track']['process']['logs']), 0)
        self.assertIsNotNone(status['track']['process']['exception'])
        self.assertTrue(self.newtask_queue.empty())

    def test_70_update_project(self):
        self.processor.project_manager.CHECK_PROJECTS_INTERVAL = 1000000
        self.processor.project_manager._check_projects()
        self.assertIsNotNone(self.processor.project_manager.get('test_broken_project'))
        # clear new task queue
        while not self.newtask_queue.empty():
            self.newtask_queue.get()
        # clear status queue
        while not self.status_queue.empty():
            self.status_queue.get()

        task = {
            "process": {
                "callback": "on_start"
            },
            "project": "test_broken_project",
            "taskid": "data:,on_start",
            "url": "data:,on_start"
        }
        fetch_result = {
            "orig_url": "data:,on_start",
            "content": "on_start",
            "headers": {},
            "status_code": 200,
            "url": "data:,on_start",
            "time": 0,
        }

        self.projectdb.update('test_broken_project', {
            'script': inspect.getsource(sample_handler),
        })

        # not update
        self.in_queue.put((task, fetch_result))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        while not self.status_queue.empty():
            status = self.status_queue.get()
        self.assertEqual(status['track']['fetch']['ok'], True)
        self.assertEqual(status['track']['process']['ok'], False)

        # updated
        task['project_updatetime'] = time.time()
        self.in_queue.put((task, fetch_result))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        while not self.status_queue.empty():
            status = self.status_queue.get()
        self.assertEqual(status['track']['fetch']['ok'], True)
        self.assertEqual(status['track']['process']['ok'], True)

        self.projectdb.update('test_broken_project', {
            'script': inspect.getsource(sample_handler)[:10],
        })

        # update with md5
        task['project_md5sum'] = 'testmd5'
        del task['project_updatetime']
        self.in_queue.put((task, fetch_result))
        time.sleep(1)
        self.assertFalse(self.status_queue.empty())
        while not self.status_queue.empty():
            status = self.status_queue.get()
        self.assertEqual(status['track']['fetch']['ok'], True)
        self.assertEqual(status['track']['process']['ok'], False)

        self.processor.project_manager.CHECK_PROJECTS_INTERVAL = 0.1

    @unittest.skipIf(six.PY3, "deprecated feature, not work for PY3")
    def test_80_import_project(self):
        self.projectdb.insert('test_project2', {
            'name': 'test_project',
            'group': 'group',
            'status': 'TODO',
            'script': inspect.getsource(sample_handler),
            'comments': 'test project',
            'rate': 1.0,
            'burst': 10,
        })
        self.projectdb.insert('test_project3', {
            'name': 'test_project',
            'group': 'group',
            'status': 'TODO',
            'script': inspect.getsource(sample_handler),
            'comments': 'test project',
            'rate': 1.0,
            'burst': 10,
        })

        from projects import test_project
        self.assertIsNotNone(test_project)
        self.assertIsNotNone(test_project.Handler)

        from projects.test_project2 import Handler
        self.assertIsNotNone(Handler)

        import projects.test_project3
        self.assertIsNotNone(projects.test_project3.Handler)
