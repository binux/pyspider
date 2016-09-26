#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-11-11 20:52:53

import os
import time
import unittest2 as unittest
import logging.config
logging.config.fileConfig("pyspider/logging.conf")

import shutil
from pyspider.database.sqlite import resultdb
from pyspider.result.result_worker import ResultWorker
from pyspider.libs.multiprocessing_queue import Queue
from pyspider.libs.utils import run_in_thread


class TestProcessor(unittest.TestCase):
    resultdb_path = './data/tests/result.db'

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/tests/', ignore_errors=True)
        os.makedirs('./data/tests/')

        def get_resultdb():
            return resultdb.ResultDB(self.resultdb_path)
        self.resultdb = get_resultdb()
        self.inqueue = Queue(10)

        def run_result_worker():
            self.result_worker = ResultWorker(get_resultdb(), self.inqueue)
            self.result_worker.run()
        self.process = run_in_thread(run_result_worker)
        time.sleep(1)

    @classmethod
    def tearDownClass(self):
        if self.process.is_alive():
            self.result_worker.quit()
            self.process.join(2)
        assert not self.process.is_alive()
        shutil.rmtree('./data/tests/', ignore_errors=True)

    def test_10_bad_result(self):
        self.inqueue.put(({'project': 'test_project'}, {}))
        self.resultdb._list_project()
        self.assertEqual(len(self.resultdb.projects), 0)
        self.assertEqual(self.resultdb.count('test_project'), 0)

    def test_10_bad_result_2(self):
        self.inqueue.put(({'project': 'test_project'}, {'a': 'b'}))
        self.resultdb._list_project()
        self.assertEqual(len(self.resultdb.projects), 0)
        self.assertEqual(self.resultdb.count('test_project'), 0)

    def test_20_insert_result(self):
        data = {
            'a': 'b'
        }
        self.inqueue.put(({
            'project': 'test_project',
            'taskid': 'id1',
            'url': 'url1'
        }, data))
        time.sleep(0.5)
        self.resultdb._list_project()
        self.assertEqual(len(self.resultdb.projects), 1)
        self.assertEqual(self.resultdb.count('test_project'), 1)

        result = self.resultdb.get('test_project', 'id1')
        self.assertEqual(result['result'], data)

    def test_30_overwrite(self):
        self.inqueue.put(({
            'project': 'test_project',
            'taskid': 'id1',
            'url': 'url1'
        }, "abc"))
        time.sleep(0.1)
        result = self.resultdb.get('test_project', 'id1')
        self.assertEqual(result['result'], "abc")

    def test_40_insert_list(self):
        self.inqueue.put(({
            'project': 'test_project',
            'taskid': 'id2',
            'url': 'url1'
        }, ['a', 'b']))
        time.sleep(0.1)
        result = self.resultdb.get('test_project', 'id2')
        self.assertEqual(result['result'], ['a', 'b'])
