#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 22:37:13

import os
import time
import unittest

import database
from database.base.taskdb import TaskDB
from database.base.projectdb import ProjectDB

class TestTaskDB(object):
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
                    'exception': u"中文",
                    },
                },
            'lastcrawltime': time.time(),
            'updatetime': time.time(),
            }

    @classmethod
    def setUpClass(self):
        raise NotImplemented()

    @classmethod
    def tearDownClass(self):
        raise NotImplemented()

    # this test not works for mongodb
    #def test_10_create_project(self):
        #with self.assertRaises(AssertionError):
            #self.taskdb._create_project('abc.abc')
        #self.taskdb._create_project('abc')
        #self.taskdb._list_project()
        #self.assertEqual(len(self.taskdb.projects), 1)
        #self.assertIn('abc', self.taskdb.projects)

    def test_20_insert(self):
        self.taskdb.insert('project', 'taskid', self.sample_task)
        self.taskdb.insert('project', 'taskid2', self.sample_task)


    def test_25_get_task(self):
        task = self.taskdb.get_task('project', 'taskid2')
        self.assertEqual(task['taskid'], 'taskid2')
        self.assertEqual(task['status'], self.taskdb.FAILED)
        self.assertEqual(task['schedule'], self.sample_task['schedule'])
        self.assertEqual(task['fetch'], self.sample_task['fetch'])
        self.assertEqual(task['process'], self.sample_task['process'])
        self.assertEqual(task['track'], self.sample_task['track'])

        task = self.taskdb.get_task('project', 'taskid1', fields=['status'])
        self.assertIsNone(task)

        task = self.taskdb.get_task('project', 'taskid', fields=['taskid', 'track', ])
        self.assertIn('track', task)
        self.assertNotIn('project', task)

    def test_30_status_count(self):
        status = self.taskdb.status_count('abc')
        self.assertEqual(status, {})
        status = self.taskdb.status_count('project')
        self.assertEqual(status, {self.taskdb.FAILED: 2})

    def test_40_update_and_status_count(self):
        self.taskdb.update('project', 'taskid', status=self.taskdb.ACTIVE)
        status = self.taskdb.status_count('project')
        self.assertEqual(status, {self.taskdb.ACTIVE: 1, self.taskdb.FAILED: 1})

        self.taskdb.update('project', 'taskid', track={})
        task = self.taskdb.get_task('project', 'taskid', fields=['taskid', 'track', ])
        self.assertIn('track', task)
        self.assertEqual(task['track'], {})

    def test_50_load_tasks(self):
        tasks = list(self.taskdb.load_tasks(self.taskdb.ACTIVE))
        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task['taskid'], 'taskid')
        self.assertEqual(task['schedule'], self.sample_task['schedule'])
        self.assertEqual(task['fetch'], self.sample_task['fetch'])
        self.assertEqual(task['process'], self.sample_task['process'])
        self.assertEqual(task['track'], {})

        tasks = list(self.taskdb.load_tasks(self.taskdb.ACTIVE, project='project',
                fields=['taskid']))
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0]['taskid'], 'taskid')
        self.assertNotIn('project', tasks[0])

class TestProjectDB(object):
    sample_project = {
            'name': 'name',
            'group': 'group',
            'status': 'TODO',
            'script': 'import time\nprint time.time()',
            'comments': 'test project',
            'rate': 1.0,
            'burst': 10,
            'updatetime': time.time(),
            }

    @classmethod
    def setUpClass(self):
        raise NotImplemented()

    @classmethod
    def tearDownClass(self):
        raise NotImplemented()

    def test_10_insert(self):
        self.projectdb.insert('abc', self.sample_project)
        self.projectdb.insert(u'name中文', self.sample_project)
        project = self.projectdb.get('abc')
        self.assertIsNotNone(project)

    def test_20_get_all(self):
        projects = list(self.projectdb.get_all())
        self.assertEqual(len(projects), 2)
        project = projects[0]
        self.assertEqual(project['script'], self.sample_project['script'])
        self.assertEqual(project['rate'], self.sample_project['rate'])
        self.assertEqual(project['burst'], self.sample_project['burst'])

        projects = list(self.projectdb.get_all(fields=['name', 'script']))
        self.assertEqual(len(projects), 2)
        project = projects[1]
        self.assertIn('name', project)
        self.assertNotIn('gourp', project)

    def test_30_update(self):
        self.projectdb.update('not_found', status='RUNNING')
        project = self.projectdb.get('not_found')
        self.assertIsNone(project)

    def test_40_check_update(self):
        time.sleep(0.1)
        now = time.time()
        time.sleep(0.1)
        self.projectdb.update('abc', status='RUNNING')

        projects = list(self.projectdb.check_update(now,
            fields=['name', 'status', 'group', 'updatetime', ]))
        self.assertEqual(len(projects), 1, repr(projects))
        project = projects[0]
        self.assertEqual(project['name'], 'abc')
        self.assertEqual(project['status'], 'RUNNING')

    def test_50_get(self):
        project = self.projectdb.get('not_found')
        self.assertIsNone(project)

        project = self.projectdb.get('abc')
        self.assertEqual(project['name'], 'abc')
        self.assertEqual(project['status'], 'RUNNING')

        project = self.projectdb.get(u'name中文', ['group', 'status', 'name'])
        self.assertIn('status', project)
        self.assertNotIn('gourp', project)

class TestResultDB(object):
    @classmethod
    def setUpClass(self):
        raise NotImplemented()

    @classmethod
    def tearDownClass(self):
        raise NotImplemented()

    def test_10_save(self):
        self.resultdb.save('test_project', 'test_taskid', 'test_url', 'result')
        result = self.resultdb.get('test_project', 'test_taskid')
        self.assertEqual(result['result'], 'result')

        self.resultdb.save('test_project', 'test_taskid', 'test_url_updated', 'result_updated')
        result = self.resultdb.get('test_project', 'test_taskid')
        self.assertEqual(result['result'], 'result_updated')
        self.assertEqual(result['url'], 'test_url_updated')

    def test_20_get(self):
        result = self.resultdb.get('test_project', 'not_exists')
        self.assertIsNone(result)

        result = self.resultdb.get('not_exists', 'test_taskid')
        self.assertIsNone(result)

        result = self.resultdb.get('test_project', 'test_taskid', fields=('url', ))
        self.assertIn('url', result)
        self.assertNotIn('result', result)

    def test_30_select(self):
        for i in range(5):
            self.resultdb.save('test_project', 'test_taskid-%d' % i,
                    'test_url', 'result-%d' % i)
        ret = list(self.resultdb.select('test_project'))
        self.assertEqual(len(ret), 6)

        ret = list(self.resultdb.select('test_project', limit=4))
        self.assertEqual(len(ret), 4)

        for ret in self.resultdb.select('test_project', fields=('url', ), limit=1):
            self.assertIn('url', ret)
            self.assertNotIn('result', ret)

    def test_40_count(self):
        self.assertEqual(self.resultdb.count('test_project'), 6)


class TestSqliteTaskDB(TestTaskDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.taskdb = database.connect_database('sqlite+taskdb://')

    @classmethod
    def tearDownClass(self):
        del self.taskdb


class TestSqliteProjectDB(TestProjectDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.projectdb = database.connect_database('sqlite+projectdb://')

    @classmethod
    def tearDownClass(self):
        del self.projectdb

class TestSqliteResultDB(TestResultDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.resultdb = database.connect_database('sqlite+resultdb://')

    @classmethod
    def tearDownClass(self):
        del self.resultdb


@unittest.skipIf(os.environ.get('IGNORE_MYSQL'), 'no mysql server for test.')
class TestMysqlTaskDB(TestTaskDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.taskdb = database.connect_database('mysql+taskdb://localhost/pyspider_test_taskdb')

    @classmethod
    def tearDownClass(self):
        self.taskdb._execute('DROP DATABASE pyspider_test_taskdb')

@unittest.skipIf(os.environ.get('IGNORE_MYSQL'), 'no mysql server for test.')
class TestMysqlProjectDB(TestProjectDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.projectdb = database.connect_database('mysql+projectdb://localhost/pyspider_test_projectdb')

    @classmethod
    def tearDownClass(self):
        self.projectdb._execute('DROP DATABASE pyspider_test_projectdb')

@unittest.skipIf(os.environ.get('IGNORE_MYSQL'), 'no mysql server for test.')
class TestMysqlResultDB(TestResultDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.resultdb = database.connect_database('mysql+resultdb://localhost/pyspider_test_resultdb')

    @classmethod
    def tearDownClass(self):
        self.resultdb._execute('DROP DATABASE pyspider_test_resultdb')


@unittest.skipIf(os.environ.get('IGNORE_MONGODB'), 'no mongodb server for test.')
class TestMongoDBTaskDB(TestTaskDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.taskdb = database.connect_database('mongodb+taskdb://localhost/pyspider_test_taskdb')

    @classmethod
    def tearDownClass(self):
        self.taskdb.conn.drop_database(self.taskdb.database.name)

@unittest.skipIf(os.environ.get('IGNORE_MONGODB'), 'no mongodb server for test.')
class TestMongoDBProjectDB(TestProjectDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.projectdb = database.connect_database('mongodb+projectdb://localhost/pyspider_test_projectdb')

    @classmethod
    def tearDownClass(self):
        self.projectdb.conn.drop_database(self.projectdb.database.name)

@unittest.skipIf(os.environ.get('IGNORE_MONGODB'), 'no mongodb server for test.')
class TestMongoDBResultDB(TestResultDB, unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.resultdb = database.connect_database('mongodb+resultdb://localhost/pyspider_test_resultdb')

    @classmethod
    def tearDownClass(self):
        self.resultdb.conn.drop_database(self.resultdb.database.name)

if __name__ == '__main__':
    unittest.main()
