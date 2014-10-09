#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 22:37:13

import os
import time
import shutil
import unittest
import logging
import logging.config
logging.config.fileConfig("logging.conf")


from scheduler.task_queue import TaskQueue
class TestTaskQueue(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.task_queue = TaskQueue()
        self.task_queue.rate = 100000
        self.task_queue.burst = 100000
        self.task_queue.processing_timeout = 0.2

        self.task_queue.put('a3', 2, time.time()+0.1)
        self.task_queue.put('a1', 1)
        self.task_queue.put('a2', 3)

    def test_1_priority_queue(self):
        self.assertEqual(self.task_queue.get(), 'a2')

    def test_2_time_queue(self):
        time.sleep(0.1)
        self.task_queue.check_update()
        self.assertEqual(self.task_queue.get(), 'a3')
        self.assertEqual(self.task_queue.get(), 'a1')

    def test_3_processing_queue(self):
        time.sleep(0.1)
        self.task_queue.check_update()
        self.assertEqual(self.task_queue.get(), 'a2')
        self.assertEqual(len(self.task_queue), 0)

    def test_4_done(self):
        self.task_queue.done('a2')
        self.task_queue.done('a1')
        time.sleep(0.1)
        self.task_queue.check_update()
        self.assertEqual(self.task_queue.get(), 'a3')
        self.assertEqual(self.task_queue.get(), None)


from scheduler.token_bucket import Bucket
class TestBucket(unittest.TestCase):
    def test_bucket(self):
        bucket = Bucket(100, 1000)
        self.assertEqual(bucket.get(), 1000)
        time.sleep(0.1)
        self.assertEqual(bucket.get(), 1000)
        bucket.desc(100)
        self.assertEqual(bucket.get(), 900)
        time.sleep(0.1)
        self.assertAlmostEqual(bucket.get(), 910, 0)
        time.sleep(0.1)
        self.assertAlmostEqual(bucket.get(), 920, 0)


import xmlrpclib
from multiprocessing import Queue
from scheduler.scheduler import Scheduler
from database.sqlite import taskdb, projectdb
from libs.utils import run_in_subprocess, run_in_thread
class TestScheduler(unittest.TestCase):
    taskdb_path = './test/data/task.db'
    projectdb_path = './test/data/project.db'
    check_project_time = 1
    scheduler_xmlrpc_port = 23333

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./test/data/', ignore_errors=True)
        os.makedirs('./test/data/')

        def get_taskdb():
            return taskdb.TaskDB(self.taskdb_path)
        self.taskdb = get_taskdb()

        def get_projectdb():
            return projectdb.ProjectDB(self.projectdb_path)
        self.projectdb = get_projectdb()

        self.newtask_queue = Queue(10)
        self.status_queue = Queue(10)
        self.scheduler2fetcher = Queue(10)
        self.rpc = xmlrpclib.ServerProxy('http://localhost:%d' % self.scheduler_xmlrpc_port)

        def run_scheduler():
            scheduler = Scheduler(taskdb=get_taskdb(), projectdb=get_projectdb(),
                    newtask_queue=self.newtask_queue, status_queue=self.status_queue,
                    out_queue=self.scheduler2fetcher, data_path="./test/data/")
            scheduler.UPDATE_PROJECT_INTERVAL = 0.1
            scheduler.LOOP_INTERVAL = 0.1
            scheduler.INQUEUE_LIMIT = 10
            scheduler._last_tick = time.time() # not dispatch cronjob
            run_in_thread(scheduler.xmlrpc_run, port=self.scheduler_xmlrpc_port)
            scheduler.run()

        self.process = run_in_subprocess(run_scheduler)
        time.sleep(1)

    @classmethod
    def tearDownClass(self):
        shutil.rmtree('./test/data/', ignore_errors=True)
        self.process.terminate()

    def test_10_new_task_ignore(self):
        self.newtask_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url'
            })
        self.assertEqual(self.rpc.size(), 0)

    def test_20_new_project(self):
        self.projectdb.insert('test_project', {
                'name': 'test_project',
                'group': 'group',
                'status': 'TODO',
                'script': 'import time\nprint time.time()',
                'comments': 'test project',
                'rate': 1.0,
                'burst': 10,
            })

    def test_30_update_project(self):
        import Queue
        with self.assertRaises(Queue.Empty):
            task = self.scheduler2fetcher.get(timeout=0.1)
        self.projectdb.update('test_project', status="DEBUG")

        task = self.scheduler2fetcher.get(timeout=5)
        self.assertIsNotNone(task)
        self.assertEqual(task['url'], 'data:,_on_get_info')

    def test_35_new_task(self):
        time.sleep(0.2)
        self.newtask_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'fetch': {
                'data': 'abc',
                },
            'process': {
                'data': 'abc',
                },
            'schedule': {
                'age': 0,
                },
            })
        timeout = time.time() + 5
        while self.rpc.size() != 1 and timeout > time.time():
            time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 1)
        self.assertEqual(self.rpc.counter('all', 'sum')['test_project']['pending'], 1)
        self.assertEqual(self.rpc.counter('all', 'sum')['test_project']['task'], 1)

        task = self.scheduler2fetcher.get(timeout=5)
        self.assertIsNotNone(task)
        self.assertEqual(task['project'], 'test_project')
        self.assertIn('fetch', task)
        self.assertIn('process', task)
        self.assertNotIn('schedule', task)
        self.assertEqual(task['fetch']['data'], 'abc')

    def test_40_taskdone_error_no_project(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'no_project',
            'url': 'url'
            })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 0)

    def test_50_taskdone_error_no_track(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url'
            })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 0)
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'track': {}
            })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 0)

    def test_60_taskdone_failed_retry(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'track': {
                'fetch': {
                    'ok': True
                    },
                'process': {
                    'ok': False
                    },
                }
            })
        task = self.scheduler2fetcher.get(timeout=5)
        self.assertIsNotNone(task)

    def test_70_taskdone_ok(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'track': {
                'fetch': {
                    'ok': True
                    },
                'process': {
                    'ok': True
                    },
                }
            })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 0)

    def test_80_newtask_age_ignore(self):
        self.newtask_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'fetch': {
                'data': 'abc',
                },
            'process': {
                'data': 'abc',
                },
            'schedule': {
                'age': 30,
                },
            })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 0)

    def test_90_newtask_with_itag(self):
        time.sleep(0.1)
        self.newtask_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'fetch': {
                'data': 'abc',
                },
            'process': {
                'data': 'abc',
                },
            'schedule': {
                'itag': "abc",
                'retries': 1
                },
            })
        task = self.scheduler2fetcher.get(timeout=5)
        self.assertIsNotNone(task)

        self.test_70_taskdone_ok()

    def test_a10_newtask_restart_by_age(self):
        self.newtask_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'fetch': {
                'data': 'abc',
                },
            'process': {
                'data': 'abc',
                },
            'schedule': {
                'age': 0,
                'retries': 1
                },
            })
        task = self.scheduler2fetcher.get(timeout=5)
        self.assertIsNotNone(task)

    def test_a20_failed_retry(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'track': {
                'fetch': {
                    'ok': True
                    },
                'process': {
                    'ok': False
                    },
                }
            })
        task = self.scheduler2fetcher.get(timeout=5)
        self.assertIsNotNone(task)

        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'track': {
                'fetch': {
                    'ok': False
                    },
                'process': {
                    'ok': True
                    },
                }
            })
        time.sleep(0.2)

    def test_x10_inqueue_limit(self):
        self.projectdb.insert('test_inqueue_project', {
                'name': 'test_inqueue_project',
                'group': 'group',
                'status': 'DEBUG',
                'script': 'import time\nprint time.time()',
                'comments': 'test project',
                'rate': 0,
                'burst': 0,
            })
        time.sleep(0.1)
        for i in range(20):
            self.newtask_queue.put({
                'taskid': 'taskid%d' % i,
                'project': 'test_inqueue_project',
                'url': 'url',
                'schedule': {
                    'age': 3000,
                    'force_update': True,
                    },
                })
        time.sleep(1)
        self.assertEqual(self.rpc.size(), 10)

    def test_z10_startup(self):
        self.assertTrue(self.process.is_alive())

    def test_z20_quit(self):
        self.rpc._quit()
        time.sleep(0.2)
        self.assertFalse(self.process.is_alive())
        self.assertEqual(self.taskdb.get_task('test_project', 'taskid')['status'], self.taskdb.FAILED)

if __name__ == '__main__':
    unittest.main()
