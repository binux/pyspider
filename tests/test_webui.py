#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-18 21:03:22

import os
import re
import time
import json
import shutil
import unittest

from pyspider import run
from pyspider.libs import utils
from pyspider.libs.utils import run_in_thread, ObjectDict


class TestWebUI(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/tests', ignore_errors=True)
        os.makedirs('./data/tests')

        import tests.data_test_webpage
        import httpbin
        from pyspider.webui import bench_test  # flake8: noqa
        self.httpbin_thread = utils.run_in_subprocess(httpbin.app.run, port=14887, passthrough_errors=False)
        self.httpbin = 'http://127.0.0.1:14887'

        ctx = run.cli.make_context('test', [
            '--taskdb', 'sqlalchemy+sqlite+taskdb:///data/tests/task.db',
            '--projectdb', 'sqlalchemy+sqlite+projectdb:///data/tests/projectdb.db',
            '--resultdb', 'sqlalchemy+sqlite+resultdb:///data/tests/resultdb.db',
        ], None, obj=ObjectDict(testing_mode=True))
        self.ctx = run.cli.invoke(ctx)

        self.threads = []

        ctx = run.scheduler.make_context('scheduler', [], self.ctx)
        self.scheduler = scheduler = run.scheduler.invoke(ctx)
        self.threads.append(run_in_thread(scheduler.xmlrpc_run))
        self.threads.append(run_in_thread(scheduler.run))

        ctx = run.fetcher.make_context('fetcher', [
            '--xmlrpc-port', '24444',
        ], self.ctx)
        fetcher = run.fetcher.invoke(ctx)
        self.threads.append(run_in_thread(fetcher.xmlrpc_run))
        self.threads.append(run_in_thread(fetcher.run))

        ctx = run.processor.make_context('processor', [], self.ctx)
        processor = run.processor.invoke(ctx)
        self.threads.append(run_in_thread(processor.run))

        ctx = run.result_worker.make_context('result_worker', [], self.ctx)
        result_worker = run.result_worker.invoke(ctx)
        self.threads.append(run_in_thread(result_worker.run))

        ctx = run.webui.make_context('webui', [
            '--scheduler-rpc', 'http://localhost:23333/'
        ], self.ctx)
        app = run.webui.invoke(ctx)
        app.debug = True
        self.app = app.test_client()
        self.rpc = app.config['scheduler_rpc']

        time.sleep(1)

    @classmethod
    def tearDownClass(self):
        for each in self.ctx.obj.instances:
            each.quit()
        time.sleep(1)

        for thread in self.threads:
            thread.join()

        self.httpbin_thread.terminate()
        self.httpbin_thread.join()

        assert not utils.check_port_open(5000)
        assert not utils.check_port_open(23333)
        assert not utils.check_port_open(24444)
        assert not utils.check_port_open(25555)
        assert not utils.check_port_open(14887)

        shutil.rmtree('./data/tests', ignore_errors=True)

    def test_10_index_page(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'dashboard', rv.data)

    def test_20_debug(self):
        rv = self.app.get('/debug/test_project')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'debugger', rv.data)
        self.assertIn(b'var task_content = ', rv.data)
        self.assertIn(b'var script_content = ', rv.data)

        m = re.search(r'var task_content = (.*);\n', utils.text(rv.data))
        self.assertIsNotNone(m)
        self.assertIn('test_project', json.loads(m.group(1)))

        m = re.search(r'var script_content = (.*);\n', utils.text(rv.data))
        self.assertIsNotNone(m)
        self.assertIn('__START_URL__', json.loads(m.group(1)))

    def test_25_debug_post(self):
        rv = self.app.post('/debug/test_project', data={
            'project-name': 'other_project',
            'start-urls': 'http://127.0.0.1:14887/pyspider/test.html',
            'script-mode': 'script',
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'debugger', rv.data)
        self.assertIn(b'var task_content = ', rv.data)
        self.assertIn(b'var script_content = ', rv.data)

        m = re.search(r'var task_content = (.*);\n', utils.text(rv.data))
        self.assertIsNotNone(m)
        self.assertIn('test_project', m.group(1))
        self.__class__.task_content = json.loads(m.group(1))

        m = re.search(r'var script_content = (.*);\n', utils.text(rv.data))
        self.assertIsNotNone(m)
        self.assertIn('127.0.0.1:14887', m.group(1))
        self.__class__.script_content = json.loads(m.group(1))

    def test_30_run(self):
        rv = self.app.post('/debug/test_project/run', data={
            'script': self.script_content,
            'task': self.task_content
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertIn(b'follows', rv.data)
        self.assertGreater(len(data['follows']), 0)
        self.__class__.task_content2 = data['follows'][0]

    def test_32_run_bad_task(self):
        rv = self.app.post('/debug/test_project/run', data={
            'script': self.script_content,
            'task': self.task_content+'asdfasdf312!@#'
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertGreater(len(data['logs']), 0)
        self.assertEqual(len(data['follows']), 0)

    def test_33_run_bad_script(self):
        rv = self.app.post('/debug/test_project/run', data={
            'script': self.script_content+'adfasfasdf',
            'task': self.task_content
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertGreater(len(data['logs']), 0)
        self.assertEqual(len(data['follows']), 0)

    def test_35_run_http_task(self):
        rv = self.app.post('/debug/test_project/run', data={
            'script': self.script_content,
            'task': json.dumps(self.task_content2)
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertIn('follows', data)

    def test_40_save(self):
        rv = self.app.post('/debug/test_project/save', data={
            'script': self.script_content,
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ok', rv.data)

    def test_42_get(self):
        rv = self.app.get('/debug/test_project/get')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertIn('script', data)
        self.assertEqual(data['script'], self.script_content)

    def test_45_run_with_saved_script(self):
        rv = self.app.post('/debug/test_project/run', data={
            'webdav_mode': 'true',
            'script': '',
            'task': self.task_content
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertIn(b'follows', rv.data)
        self.assertGreater(len(data['follows']), 0)
        self.__class__.task_content2 = data['follows'][0]

    def test_50_index_page_list(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'"test_project"', rv.data)

    def test_52_change_status(self):
        rv = self.app.post('/update', data={
            'name': 'status',
            'value': 'RUNNING',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ok', rv.data)

    def test_55_reopen(self):
        rv = self.app.get('/debug/test_project')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'debugger', rv.data)

    def test_57_resave(self):
        rv = self.app.post('/debug/test_project/save', data={
            'script': self.script_content,
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ok', rv.data)

    def test_58_index_page_list(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'CHECKING', rv.data)

    def test_60_change_rate(self):
        rv = self.app.post('/update', data={
            'name': 'rate',
            'value': '1/4',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ok', rv.data)

    def test_70_change_status(self):
        rv = self.app.post('/update', data={
            'name': 'status',
            'value': 'RUNNING',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ok', rv.data)

    def test_80_change_group(self):
        rv = self.app.post('/update', data={
            'name': 'group',
            'value': 'test_binux',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ok', rv.data)

        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'test_binux', rv.data)

    def test_90_run(self):
        time.sleep(0.5)
        rv = self.app.post('/run', data={
            'project': 'test_project',
        })
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(utils.text(rv.data))['result'], True)

    def test_a10_counter(self):
        for i in range(30):
            time.sleep(1)
            if self.rpc.counter('5m', 'sum')\
                    .get('test_project', {}).get('success', 0) > 5:
                break

        rv = self.app.get('/counter')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertGreater(len(data), 0)
        self.assertGreater(data['test_project']['5m']['success'], 3)
        self.assertGreater(data['test_project']['1h']['success'], 3)
        self.assertGreater(data['test_project']['1d']['success'], 3)
        self.assertGreater(data['test_project']['all']['success'], 3)

    def test_a15_queues(self):
        rv = self.app.get('/queues')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertGreater(len(data), 0)
        self.assertIn('scheduler2fetcher', data)
        self.assertIn('fetcher2processor', data)
        self.assertIn('processor2result', data)
        self.assertIn('newtask_queue', data)
        self.assertIn('status_queue', data)

    def test_a20_tasks(self):
        rv = self.app.get('/tasks')
        self.assertEqual(rv.status_code, 200, rv.data)
        self.assertIn(b'SUCCESS</span>', rv.data)
        self.assertNotIn(b'>ERROR</span>', rv.data)
        m = re.search(r'/task/test_project:[^"]+', utils.text(rv.data))
        self.assertIsNotNone(m)
        self.__class__.task_url = m.group(0)
        self.assertIsNotNone(self.task_url)
        m = re.search(r'/debug/test_project[^"]+', utils.text(rv.data))
        self.assertIsNotNone(m)
        self.__class__.debug_task_url = m.group(0)
        self.assertIsNotNone(self.debug_task_url)

        rv = self.app.get('/tasks?project=test_project')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'SUCCESS</span>', rv.data)
        self.assertNotIn(b'>ERROR</span>', rv.data)

    def test_a22_active_tasks(self):
        rv = self.app.get('/active_tasks')
        data = json.loads(utils.text(rv.data))
        track = False
        self.assertGreater(len(data), 0)
        for task in data:
            for k in ('taskid', 'project', 'url', 'updatetime'):
                self.assertIn(k, task)
            if task.get('track'):
                track = True
                self.assertIn('fetch', task['track'])
                self.assertIn('ok', task['track']['fetch'])
                self.assertIn('time', task['track']['fetch'])
                self.assertIn('process', task['track'])
                self.assertIn('ok', task['track']['process'])
                self.assertIn('time', task['track']['process'])
        self.assertTrue(track)
                    

    def test_a24_task(self):
        rv = self.app.get(self.task_url)
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'lastcrawltime', rv.data)

    def test_a25_task_json(self):
        rv = self.app.get(self.task_url + '.json')
        self.assertEqual(rv.status_code, 200)
        self.assertIn('status_string', json.loads(utils.text(rv.data)))

    def test_a26_debug_task(self):
        rv = self.app.get(self.debug_task_url)
        self.assertEqual(rv.status_code, 200)

    def test_a30_results(self):
        rv = self.app.get('/results?project=test_project')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'<th>url</th>', rv.data)
        self.assertIn(b'open-url', rv.data)

    def test_a30_export_json(self):
        rv = self.app.get('/results/dump/test_project.json')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'"taskid":', rv.data)

    def test_a32_export_json_style_full(self):
        rv = self.app.get('/results/dump/test_project.json?style=full')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode('utf8'))
        self.assertGreater(len(data), 1)

    def test_a34_export_json_style_full_limit_1(self):
        rv = self.app.get('/results/dump/test_project.json?style=full&limit=1&offset=1')
        self.assertEqual(rv.status_code, 200)
        data = json.loads(rv.data.decode('utf8'))
        self.assertEqual(len(data), 1)

    def test_a40_export_url_json(self):
        rv = self.app.get('/results/dump/test_project.txt')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'"url":', rv.data)

    def test_a50_export_csv(self):
        rv = self.app.get('/results/dump/test_project.csv')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'url,title,url', rv.data)

    def test_a60_fetch_via_cannot_connect_fetcher(self):
        ctx = run.webui.make_context('webui', [
            '--fetcher-rpc', 'http://localhost:20000/',
        ], self.ctx)
        app = run.webui.invoke(ctx)
        app = app.test_client()
        rv = app.post('/debug/test_project/run', data={
            'script': self.script_content,
            'task': self.task_content
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertGreater(len(data['logs']), 0)
        self.assertEqual(len(data['follows']), 0)

    def test_a70_fetch_via_fetcher(self):
        ctx = run.webui.make_context('webui', [
            '--fetcher-rpc', 'http://localhost:24444/',
        ], self.ctx)
        app = run.webui.invoke(ctx)
        app = app.test_client()
        rv = app.post('/debug/test_project/run', data={
            'script': self.script_content,
            'task': self.task_content
        })
        self.assertEqual(rv.status_code, 200)
        data = json.loads(utils.text(rv.data))
        self.assertEqual(len(data['logs']), 0, data['logs'])
        self.assertIn(b'follows', rv.data)
        self.assertGreater(len(data['follows']), 0)

    def test_h000_auth(self):
        ctx = run.webui.make_context('webui', [
            '--scheduler-rpc', 'http://localhost:23333/',
            '--username', 'binux',
            '--password', '4321',
        ], self.ctx)
        app = run.webui.invoke(ctx)
        self.__class__.app = app.test_client()
        self.__class__.rpc = app.config['scheduler_rpc']

    def test_h005_no_such_project(self):
        rv = self.app.post('/update', data={
            'name': 'group',
            'value': 'lock',
            'pk': 'not_exist_project'
        })
        self.assertEqual(rv.status_code, 404)

    def test_h005_unknown_field(self):
        rv = self.app.post('/update', data={
            'name': 'unknown_field',
            'value': 'lock',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 400)

    def test_h005_rate_wrong_format(self):
        rv = self.app.post('/update', data={
            'name': 'rate',
            'value': 'xxx',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 400)

    def test_h010_change_group(self):
        rv = self.app.post('/update', data={
            'name': 'group',
            'value': 'lock',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ok', rv.data)

        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'lock', rv.data)

    def test_h020_change_group_lock_failed(self):
        rv = self.app.post('/update', data={
            'name': 'group',
            'value': '',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 401)

    def test_h020_change_group_lock_ok(self):
        rv = self.app.post('/update', data={
            'name': 'group',
            'value': 'test_binux',
            'pk': 'test_project'
        }, headers={
            'Authorization': 'Basic YmludXg6NDMyMQ=='
        })
        self.assertEqual(rv.status_code, 200)

    def test_h030_need_auth(self):
        ctx = run.webui.make_context('webui', [
            '--scheduler-rpc', 'http://localhost:23333/',
            '--username', 'binux',
            '--password', '4321',
            '--need-auth',
        ], self.ctx)
        app = run.webui.invoke(ctx)
        self.__class__.app = app.test_client()
        self.__class__.rpc = app.config['scheduler_rpc']

    def test_h040_auth_fail(self):
        rv = self.app.get('/')
        self.assertEqual(rv.status_code, 401)

    def test_h050_auth_fail2(self):
        rv = self.app.get('/', headers={
            'Authorization': 'Basic Ymlasdfsd'
        })
        self.assertEqual(rv.status_code, 401)

    def test_h060_auth_fail3(self):
        rv = self.app.get('/', headers={
            'Authorization': 'Basic YmludXg6MQ=='
        })
        self.assertEqual(rv.status_code, 401)

    def test_h070_auth_ok(self):
        rv = self.app.get('/', headers={
            'Authorization': 'Basic YmludXg6NDMyMQ=='
        })
        self.assertEqual(rv.status_code, 200)

    def test_x0_disconnected_scheduler(self):
        ctx = run.webui.make_context('webui', [
            '--scheduler-rpc', 'http://localhost:23458/'
        ], self.ctx)
        app = run.webui.invoke(ctx)
        self.__class__.app = app.test_client()
        self.__class__.rpc = app.config['scheduler_rpc']

    def test_x10_project_update(self):
        rv = self.app.post('/update', data={
            'name': 'status',
            'value': 'RUNNING',
            'pk': 'test_project'
        })
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn(b'ok', rv.data)

    def test_x20_counter(self):
        rv = self.app.get('/counter?time=5m&type=sum')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(utils.text(rv.data)), {})

    def test_x30_run_not_exists_project(self):
        rv = self.app.post('/run', data={
            'project': 'not_exist_project',
        })
        self.assertEqual(rv.status_code, 404)

    def test_x30_run(self):
        rv = self.app.post('/run', data={
            'project': 'test_project',
        })
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(json.loads(utils.text(rv.data))['result'], False)

    def test_x40_debug_save(self):
        rv = self.app.post('/debug/test_project/save', data={
            'script': self.script_content,
        })
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn(b'ok', rv.data)

    def test_x50_tasks(self):
        rv = self.app.get('/tasks')
        self.assertEqual(rv.status_code, 502)

    def test_x60_robots(self):
        rv = self.app.get('/robots.txt')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'ser-agent', rv.data)

    def test_x70_bench(self):
        rv = self.app.get('/bench?total=10&show=5')
        self.assertEqual(rv.status_code, 200)
