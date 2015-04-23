#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 22:37:13

import os
import time
import shutil
import unittest2 as unittest
import logging
import logging.config
logging.config.fileConfig("pyspider/logging.conf")

from pyspider.scheduler.task_queue import TaskQueue


class TestTaskQueue(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.task_queue = TaskQueue()
        self.task_queue.rate = 100000
        self.task_queue.burst = 100000
        self.task_queue.processing_timeout = 0.5

    def test_10_put(self):
        self.task_queue.put('a3', 0, time.time() + 0.5)
        self.task_queue.put('a4', 3, time.time() + 0.2)
        self.task_queue.put('a2', 0)
        self.task_queue.put('a1', 1)
        self.assertEqual(self.task_queue.size(), 4)

    def test_20_update(self):
        self.task_queue.put('a2', 4)
        self.assertEqual(self.task_queue.size(), 4)
        self.task_queue.put('a3', 2, 0)
        self.assertEqual(self.task_queue.size(), 4)

    def test_30_get_from_priority_queue(self):
        self.assertEqual(self.task_queue.get(), 'a2')
        self.assertEqual(self.task_queue.size(), 4)

    def test_40_time_queue_1(self):
        self.task_queue.check_update()
        self.assertEqual(self.task_queue.get(), 'a3')
        self.assertEqual(self.task_queue.size(), 4)

    def test_50_time_queue_2(self):
        time.sleep(0.3)
        self.task_queue.check_update()
        self.assertEqual(self.task_queue.get(), 'a4')
        self.assertEqual(self.task_queue.get(), 'a1')
        self.assertEqual(self.task_queue.size(), 4)

    def test_60_processing_queue(self):
        time.sleep(0.5)
        self.task_queue.check_update()
        self.assertEqual(self.task_queue.get(), 'a2')
        self.assertEqual(len(self.task_queue), 4)
        self.assertEqual(self.task_queue.get(), 'a4')
        self.assertEqual(self.task_queue.get(), 'a3')
        self.assertEqual(self.task_queue.get(), 'a1')
        self.assertEqual(len(self.task_queue), 4)

    def test_70_done(self):
        self.assertTrue(self.task_queue.done('a2'))
        self.assertTrue(self.task_queue.done('a1'))
        self.assertEqual(len(self.task_queue), 2)
        self.assertTrue(self.task_queue.done('a4'))
        self.assertTrue(self.task_queue.done('a3'))
        self.assertEqual(len(self.task_queue), 0)


from pyspider.scheduler.token_bucket import Bucket


class TestBucket(unittest.TestCase):

    def test_bucket(self):
        bucket = Bucket(100, 1000)
        self.assertEqual(bucket.get(), 1000)
        time.sleep(0.1)
        self.assertEqual(bucket.get(), 1000)
        bucket.desc(100)
        self.assertEqual(bucket.get(), 900)
        time.sleep(0.1)
        self.assertAlmostEqual(bucket.get(), 910, delta=2)
        time.sleep(0.1)
        self.assertAlmostEqual(bucket.get(), 920, delta=2)


try:
    from six.moves import xmlrpc_client
except ImportError:
    import xmlrpclib as xmlrpc_client
from multiprocessing import Queue
from pyspider.scheduler.scheduler import Scheduler
from pyspider.database.sqlite import taskdb, projectdb, resultdb
from pyspider.libs.utils import run_in_thread


class TestScheduler(unittest.TestCase):
    taskdb_path = './data/tests/task.db'
    projectdb_path = './data/tests/project.db'
    resultdb_path = './data/tests/result.db'
    check_project_time = 1
    scheduler_xmlrpc_port = 23333

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/tests', ignore_errors=True)
        os.makedirs('./data/tests')

        def get_taskdb():
            return taskdb.TaskDB(self.taskdb_path)
        self.taskdb = get_taskdb()

        def get_projectdb():
            return projectdb.ProjectDB(self.projectdb_path)
        self.projectdb = get_projectdb()

        def get_resultdb():
            return resultdb.ResultDB(self.resultdb_path)
        self.resultdb = get_resultdb()

        self.newtask_queue = Queue(10)
        self.status_queue = Queue(10)
        self.scheduler2fetcher = Queue(10)
        self.rpc = xmlrpc_client.ServerProxy('http://localhost:%d' % self.scheduler_xmlrpc_port)

        def run_scheduler():
            scheduler = Scheduler(taskdb=get_taskdb(), projectdb=get_projectdb(),
                                  newtask_queue=self.newtask_queue, status_queue=self.status_queue,
                                  out_queue=self.scheduler2fetcher, data_path="./data/tests/",
                                  resultdb=get_resultdb())
            scheduler.UPDATE_PROJECT_INTERVAL = 0.1
            scheduler.LOOP_INTERVAL = 0.1
            scheduler.INQUEUE_LIMIT = 10
            Scheduler.DELETE_TIME = 0
            scheduler._last_tick = int(time.time())  # not dispatch cronjob
            run_in_thread(scheduler.xmlrpc_run, port=self.scheduler_xmlrpc_port)
            scheduler.run()

        self.process = run_in_thread(run_scheduler)
        time.sleep(1)

    @classmethod
    def tearDownClass(self):
        if self.process.is_alive():
            self.rpc._quit()
            self.process.join(5)
        assert not self.process.is_alive()
        shutil.rmtree('./data/tests', ignore_errors=True)
        time.sleep(1)

    def test_10_new_task_ignore(self):
        self.newtask_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url'
        })
        self.assertEqual(self.rpc.size(), 0)
        self.assertEqual(len(self.rpc.get_active_tasks()), 0)

    def test_20_new_project(self):
        self.projectdb.insert('test_project', {
            'name': 'test_project',
            'group': 'group',
            'status': 'TODO',
            'script': 'import time\nprint(time.time())',
            'comments': 'test project',
            'rate': 1.0,
            'burst': 10,
        })

    def test_30_update_project(self):
        from six.moves import queue as Queue
        with self.assertRaises(Queue.Empty):
            task = self.scheduler2fetcher.get(timeout=1)
        self.projectdb.update('test_project', status="DEBUG")
        time.sleep(0.1)
        self.rpc.update_project()

        task = self.scheduler2fetcher.get(timeout=10)
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

        time.sleep(0.5)
        task = self.scheduler2fetcher.get(timeout=10)
        self.assertGreater(len(self.rpc.get_active_tasks()), 0)
        self.assertIsNotNone(task)
        self.assertEqual(task['project'], 'test_project')
        self.assertIn('fetch', task)
        self.assertIn('process', task)
        self.assertNotIn('schedule', task)
        self.assertEqual(task['fetch']['data'], 'abc')

    def test_37_force_update_processing_task(self):
        self.newtask_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url_force_update',
            'schedule': {
                'age': 0,
                'force_update': True,
            },
        })
        time.sleep(0.2)
        # it should not block next

    def test_40_taskdone_error_no_project(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'no_project',
            'url': 'url'
        })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 1)

    def test_50_taskdone_error_no_track(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url'
        })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 1)
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'track': {}
        })
        time.sleep(0.1)
        self.assertEqual(self.rpc.size(), 1)

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
        task = self.scheduler2fetcher.get(timeout=10)
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
        time.sleep(0.2)
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

    def test_82_newtask_via_rpc(self):
        self.rpc.newtask({
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
        task = self.scheduler2fetcher.get(timeout=10)
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
        task = self.scheduler2fetcher.get(timeout=10)
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
        task = self.scheduler2fetcher.get(timeout=10)
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
                    'ok': False
                },
            }
        })

        from six.moves import queue as Queue
        with self.assertRaises(Queue.Empty):
            self.scheduler2fetcher.get(timeout=5)

    def test_a30_task_verify(self):
        self.assertFalse(self.rpc.newtask({
            #'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
        }))
        self.assertFalse(self.rpc.newtask({
            'taskid': 'taskid',
            #'project': 'test_project',
            'url': 'url',
        }))
        self.assertFalse(self.rpc.newtask({
            'taskid': 'taskid',
            'project': 'test_project',
            #'url': 'url',
        }))
        self.assertFalse(self.rpc.newtask({
            'taskid': 'taskid',
            'project': 'not_exist_project',
            'url': 'url',
        }))
        self.assertTrue(self.rpc.newtask({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
        }))

    def test_a40_success_recrawl(self):
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
                'retries': 1,
                'auto_recrawl': True,
            },
        })
        task = self.scheduler2fetcher.get(timeout=10)
        self.assertIsNotNone(task)

        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'schedule': {
                'age': 0,
                'retries': 1,
                'auto_recrawl': True,
            },
            'track': {
                'fetch': {
                    'ok': True
                },
                'process': {
                    'ok': True
                },
            }
        })
        task = self.scheduler2fetcher.get(timeout=10)
        self.assertIsNotNone(task)

    def test_a50_failed_recrawl(self):
        for i in range(3):
            self.status_queue.put({
                'taskid': 'taskid',
                'project': 'test_project',
                'url': 'url',
                'schedule': {
                    'age': 0,
                    'retries': 1,
                    'auto_recrawl': True,
                },
                'track': {
                    'fetch': {
                        'ok': True
                    },
                    'process': {
                        'ok': False
                    },
                }
            })
            task = self.scheduler2fetcher.get(timeout=10)
            self.assertIsNotNone(task)

    def test_a60_disable_recrawl(self):
        self.status_queue.put({
            'taskid': 'taskid',
            'project': 'test_project',
            'url': 'url',
            'schedule': {
                'age': 0,
                'retries': 1,
            },
            'track': {
                'fetch': {
                    'ok': True
                },
                'process': {
                    'ok': True
                },
            }
        })

        from six.moves import queue as Queue
        with self.assertRaises(Queue.Empty):
            self.scheduler2fetcher.get(timeout=5)

    def test_x10_inqueue_limit(self):
        self.projectdb.insert('test_inqueue_project', {
            'name': 'test_inqueue_project',
            'group': 'group',
            'status': 'DEBUG',
            'script': 'import time\nprint(time.time())',
            'comments': 'test project',
            'rate': 0,
            'burst': 0,
        })
        time.sleep(0.1)
        self.assertLess(self.rpc.size(), 10)
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

    def test_x20_delete_project(self):
        self.assertIsNotNone(self.projectdb.get('test_inqueue_project'))
        self.assertIsNotNone(self.taskdb.get_task('test_inqueue_project', 'taskid1'))
        self.projectdb.update('test_inqueue_project', status="STOP", group="lock,delete")
        time.sleep(1)
        self.assertIsNone(self.projectdb.get('test_inqueue_project'))
        self.taskdb._list_project()
        self.assertIsNone(self.taskdb.get_task('test_inqueue_project', 'taskid1'))

    def test_z10_startup(self):
        self.assertTrue(self.process.is_alive())

    def test_z20_quit(self):
        self.rpc._quit()
        time.sleep(0.2)
        self.assertFalse(self.process.is_alive())
        self.assertEqual(
            self.taskdb.get_task('test_project', 'taskid')['status'],
            self.taskdb.SUCCESS
        )

if __name__ == '__main__':
    unittest.main()
