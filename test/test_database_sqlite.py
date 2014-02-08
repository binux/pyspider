#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 22:37:13


import time
import unittest
from database.sqlite.taskdb import TaskDB


class TestTaskDB(unittest.TestCase):
    sample_task = {
            'taskid': 'taskid',
            'project': 'project',
            'url': 'www.baidu.com/',
            'status': TaskDB.FAILED,
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
            'track': {
                'fetch': {
                    'ok': True,
                    'time': 300,
                    'status_code': 200,
                    'headers': {
                        'Content-Type': 'plain/html', 
                        },
                    'encoding': 'utf8',
                    #'content': 'asdfasdfasdfasdf',
                    },
                'process': {
                    'ok': False,
                    'time': 10,
                    'follows': 3,
                    'outputs': 5,
                    'exception': "?",
                    },
                },
            'lastcrawltime': time.time(),
            'updatetime': time.time(),
            }

    def setUp(self):
        pass

    def test_create_project(self):
        taskdb = TaskDB(':memory:')
        with self.assertRaises(AssertionError):
            taskdb._create_project('abc.abc')
        taskdb._create_project('abc')
        taskdb._list_project()
        self.assertSetEqual(taskdb.projects, set(('abc', )))

    def test_other(self):
        taskdb = TaskDB(':memory:')

        # insert
        taskdb.insert('project', 'taskid', self.sample_task)
        taskdb.insert('project', 'taskid2', self.sample_task)

        # status_count
        status = taskdb.status_count('abc')
        self.assertEqual(status, {})
        status = taskdb.status_count('project')
        self.assertEqual(status, {taskdb.FAILED: 2})

        # update & status_count
        taskdb.update('project', 'taskid', status=taskdb.ACTIVE)
        status = taskdb.status_count('project')
        self.assertEqual(status, {taskdb.ACTIVE: 1, taskdb.FAILED: 1})

        # load tasks
        taskdb.update('project', 'taskid', track={})
        tasks = list(taskdb.load_tasks(taskdb.ACTIVE))
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task['taskid'], 'taskid')
        self.assertEqual(task['schedule'], self.sample_task['schedule'])
        self.assertEqual(task['fetch'], self.sample_task['fetch'])
        self.assertEqual(task['process'], self.sample_task['process'])
        self.assertEqual(task['track'], {})

        tasks = list(taskdb.load_tasks(taskdb.ACTIVE, project='project',
                fields=['taskid']))
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['taskid'], 'taskid')
        self.assertNotIn('project', tasks[0])

        # get_task
        task = taskdb.get_task('project', 'taskid1', fields=['status'])
        self.assertIsNone(task)

        task = taskdb.get_task('project', 'taskid2')
        self.assertEqual(task['taskid'], 'taskid2')
        self.assertEqual(task['status'], taskdb.FAILED)
        self.assertEqual(task['schedule'], self.sample_task['schedule'])
        self.assertEqual(task['fetch'], self.sample_task['fetch'])
        self.assertEqual(task['process'], self.sample_task['process'])
        self.assertEqual(task['track'], self.sample_task['track'])

        task = taskdb.get_task('project', 'taskid', fields=['status'])
        self.assertEqual(task['status'], taskdb.ACTIVE)
        self.assertNotIn('taskid', task)


if __name__ == '__main__':
    unittest.main()
