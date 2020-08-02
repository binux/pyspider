#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-21 22:32:35

from __future__ import print_function

import os
import sys
import six
import time
import json
import signal
import shutil
import inspect
import requests
import unittest

from pyspider import run
from pyspider.libs import utils
from tests import data_sample_handler

class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/tests', ignore_errors=True)
        os.makedirs('./data/tests')

        import tests.data_test_webpage
        import httpbin
        self.httpbin_thread = utils.run_in_subprocess(httpbin.app.run, port=14887, passthrough_errors=False)
        self.httpbin = 'http://127.0.0.1:14887'

    @classmethod
    def tearDownClass(self):
        self.httpbin_thread.terminate()
        self.httpbin_thread.join()

        assert not utils.check_port_open(5000)
        assert not utils.check_port_open(23333)
        assert not utils.check_port_open(24444)
        assert not utils.check_port_open(25555)
        assert not utils.check_port_open(14887)

        shutil.rmtree('./data/tests', ignore_errors=True)

    def test_10_cli(self):
        ctx = run.cli.make_context('test', [], None, obj=dict(testing_mode=True))
        ctx = run.cli.invoke(ctx)
        self.assertEqual(ctx.obj.debug, False)
        for db in ('taskdb', 'projectdb', 'resultdb'):
            self.assertIsNotNone(getattr(ctx.obj, db))
        for name in ('newtask_queue', 'status_queue', 'scheduler2fetcher',
                     'fetcher2processor', 'processor2result'):
            self.assertIsNotNone(getattr(ctx.obj, name))
        self.assertEqual(len(ctx.obj.instances), 0)

    def test_20_cli_config(self):
        with open('./data/tests/config.json', 'w') as fp:
            json.dump({
                'debug': True,
                'taskdb': 'mysql+taskdb://localhost:23456/taskdb',
                'amqp-url': 'amqp://guest:guest@localhost:23456/%%2F'
            }, fp)
        ctx = run.cli.make_context('test',
                                   ['--config', './data/tests/config.json'],
                                   None, obj=dict(testing_mode=True))
        ctx = run.cli.invoke(ctx)
        self.assertEqual(ctx.obj.debug, True)

        import mysql.connector
        with self.assertRaises(mysql.connector.Error):
            ctx.obj.taskdb

        with self.assertRaises(Exception):
            ctx.obj.newtask_queue

    def test_30_cli_command_line(self):
        ctx = run.cli.make_context(
            'test',
            ['--projectdb', 'mongodb+projectdb://localhost:23456/projectdb'],
            None,
            obj=dict(testing_mode=True)
        )
        ctx = run.cli.invoke(ctx)

        from pymongo.errors import ConnectionFailure
        with self.assertRaises(ConnectionFailure):
            ctx.obj.projectdb

    def test_30a_cli_command_line(self):
        ctx = run.cli.make_context(
            'test',
            ['--projectdb', 'couchdb+projectdb://localhost:5984/projectdb'],
            None,
            obj=dict(testing_mode=True)
        )
        ctx = run.cli.invoke(ctx)

        with self.assertRaises(Exception):
            # TODO: MORE SPECIFIC
            ctx.obj.projectdb

    def test_40_cli_env(self):
        try:
            os.environ['RESULTDB'] = 'sqlite+resultdb://'
            ctx = run.cli.make_context('test', [], None,
                                       obj=dict(testing_mode=True))
            ctx = run.cli.invoke(ctx)

            from pyspider.database.sqlite import resultdb
            self.assertIsInstance(ctx.obj.resultdb, resultdb.ResultDB)
        finally:
            del os.environ['RESULTDB']

    @unittest.skipIf(os.environ.get('IGNORE_RABBITMQ') or os.environ.get('IGNORE_ALL'), 'no rabbitmq server for test.')
    def test_50_docker_rabbitmq(self):
        try:
            os.environ['RABBITMQ_NAME'] = 'rabbitmq'
            os.environ['RABBITMQ_PORT_5672_TCP_ADDR'] = 'localhost'
            os.environ['RABBITMQ_PORT_5672_TCP_PORT'] = '5672'
            ctx = run.cli.make_context('test', [], None,
                                       obj=dict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            queue = ctx.obj.newtask_queue
            queue.put('abc')
            queue.delete()
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['RABBITMQ_NAME']
            del os.environ['RABBITMQ_PORT_5672_TCP_ADDR']
            del os.environ['RABBITMQ_PORT_5672_TCP_PORT']

    @unittest.skipIf(os.environ.get('IGNORE_MONGODB') or os.environ.get('IGNORE_ALL'), 'no mongodb server for test.')
    def test_60_docker_mongodb(self):
        try:
            os.environ['MONGODB_NAME'] = 'mongodb'
            os.environ['MONGODB_PORT_27017_TCP_ADDR'] = 'localhost'
            os.environ['MONGODB_PORT_27017_TCP_PORT'] = '27017'
            ctx = run.cli.make_context('test', [], None,
                                       obj=dict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            ctx.obj.resultdb
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['MONGODB_NAME']
            del os.environ['MONGODB_PORT_27017_TCP_ADDR']
            del os.environ['MONGODB_PORT_27017_TCP_PORT']

    @unittest.skipIf(os.environ.get('IGNORE_COUCHDB') or os.environ.get('IGNORE_ALL'), 'no couchdb server for test.')
    def test_60a_docker_couchdb(self):
        try:
            # create a test admin user
            os.environ['COUCHDB_NAME'] = 'couchdb'
            os.environ['COUCHDB_PORT_5984_TCP_ADDR'] = 'localhost'
            os.environ['COUCHDB_PORT_5984_TCP_PORT'] = '5984'
            ctx = run.cli.make_context('test', [], None,
                                       obj=dict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            ctx.obj.resultdb
        except Exception as e:
            self.assertIsNone(e)
        finally:
            # remove the test admin user
            del os.environ['COUCHDB_NAME']
            del os.environ['COUCHDB_PORT_5984_TCP_ADDR']
            del os.environ['COUCHDB_PORT_5984_TCP_PORT']

    @unittest.skip('only available in docker')
    @unittest.skipIf(os.environ.get('IGNORE_MYSQL') or os.environ.get('IGNORE_ALL'), 'no mysql server for test.')
    def test_70_docker_mysql(self):
        try:
            os.environ['MYSQL_NAME'] = 'mysql'
            os.environ['MYSQL_PORT_3306_TCP_ADDR'] = 'localhost'
            os.environ['MYSQL_PORT_3306_TCP_PORT'] = '3306'
            ctx = run.cli.make_context('test', [], None,
                                       obj=dict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            ctx.obj.resultdb
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['MYSQL_NAME']
            del os.environ['MYSQL_PORT_3306_TCP_ADDR']
            del os.environ['MYSQL_PORT_3306_TCP_PORT']

    def test_80_docker_phantomjs(self):
        try:
            os.environ['PHANTOMJS_NAME'] = 'phantomjs'
            os.environ['PHANTOMJS_PORT_25555_TCP'] = 'tpc://binux:25678'
            ctx = run.cli.make_context('test', [], None,
                                       obj=dict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            self.assertEqual(ctx.obj.phantomjs_proxy, 'binux:25678')
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['PHANTOMJS_NAME']
            del os.environ['PHANTOMJS_PORT_25555_TCP']

    def test_90_docker_scheduler(self):
        try:
            os.environ['SCHEDULER_PORT_23333_TCP_ADDR'] = 'scheduler'
            os.environ['SCHEDULER_PORT_23333_TCP_PORT'] = '23333'

            ctx = run.cli.make_context('test', [], None,
                                       obj=dict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            webui = run.cli.get_command(ctx, 'webui')
            webui_ctx = webui.make_context('webui', [], ctx)
            app = webui.invoke(webui_ctx)
            rpc = app.config['scheduler_rpc']
            self.assertEqual(rpc._ServerProxy__host, '{}:{}'.format(os.environ['SCHEDULER_PORT_23333_TCP_ADDR'],
                                                                    os.environ['SCHEDULER_PORT_23333_TCP_PORT']))
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['SCHEDULER_PORT_23333_TCP_ADDR']
            del os.environ['SCHEDULER_PORT_23333_TCP_PORT']

    def test_a100_all(self):
        import subprocess
        #cmd = [sys.executable]
        cmd = ['coverage', 'run']
        p = subprocess.Popen(cmd+[
            inspect.getsourcefile(run),
            '--taskdb', 'sqlite+taskdb:///data/tests/all_test_task.db',
            '--resultdb', 'sqlite+resultdb:///data/tests/all_test_result.db',
            '--projectdb', 'local+projectdb://'+inspect.getsourcefile(data_sample_handler),
            'all',
        ], close_fds=True, preexec_fn=os.setsid)

        try:
            limit = 30
            while limit >= 0:
                time.sleep(3)
                # click run
                try:
                    requests.post('http://localhost:5000/run', data={
                        'project': 'data_sample_handler',
                    })
                except requests.exceptions.ConnectionError:
                    limit -= 1
                    continue
                break

            limit = 30
            data = requests.get('http://localhost:5000/counter')
            self.assertEqual(data.status_code, 200)
            while data.json().get('data_sample_handler', {}).get('5m', {}).get('success', 0) < 5:
                time.sleep(1)
                data = requests.get('http://localhost:5000/counter')
                limit -= 1
                if limit <= 0:
                    break

            self.assertGreater(limit, 0)
            rv = requests.get('http://localhost:5000/results?project=data_sample_handler')
            self.assertIn('<th>url</th>', rv.text)
            self.assertIn('class=url', rv.text)
        except:
            raise
        finally:
            time.sleep(1)
            os.killpg(p.pid, signal.SIGTERM)
            p.wait()

    def test_a110_one(self):
        pid, fd = os.forkpty()
        #cmd = [sys.executable]
        cmd = ['coverage', 'run']
        cmd += [
            inspect.getsourcefile(run),
            'one',
            '-i',
            inspect.getsourcefile(data_sample_handler)
        ]

        if pid == 0:
            # child
            os.execvp(cmd[0], cmd)
        else:
            # parent
            def wait_text(timeout=1):
                import select
                text = []
                while True:
                    rl, wl, xl = select.select([fd], [], [], timeout)
                    if not rl:
                        break
                    try:
                        t = os.read(fd, 1024)
                    except OSError:
                        break
                    if not t:
                        break
                    t = utils.text(t)
                    text.append(t)
                    print(t, end='')
                return ''.join(text)

            text = wait_text(3)
            self.assertIn('new task data_sample_handler:on_start', text)
            self.assertIn('pyspider shell', text)

            os.write(fd, utils.utf8('run()\n'))
            text = wait_text()
            self.assertIn('task done data_sample_handler:on_start', text)

            os.write(fd, utils.utf8('crawl("%s/pyspider/test.html")\n' % self.httpbin))
            text = wait_text()
            self.assertIn('/robots.txt', text)

            os.write(fd, utils.utf8('crawl("%s/links/10/0")\n' % self.httpbin))
            text = wait_text()
            if '"title": "Links"' not in text:
                os.write(fd, utils.utf8('crawl("%s/links/10/1")\n' % self.httpbin))
                text = wait_text()
                self.assertIn('"title": "Links"', text)

            os.write(fd, utils.utf8('crawl("%s/404")\n' % self.httpbin))
            text = wait_text()
            self.assertIn('task retry', text)

            os.write(fd, b'quit_pyspider()\n')
            text = wait_text()
            self.assertIn('scheduler exiting...', text)
            os.close(fd)
            os.kill(pid, signal.SIGINT)

class TestSendMessage(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/tests', ignore_errors=True)
        os.makedirs('./data/tests')

        ctx = run.cli.make_context('test', [
            '--taskdb', 'sqlite+taskdb:///data/tests/task.db',
            '--projectdb', 'sqlite+projectdb:///data/tests/projectdb.db',
            '--resultdb', 'sqlite+resultdb:///data/tests/resultdb.db',
        ], None, obj=dict(testing_mode=True))
        self.ctx = run.cli.invoke(ctx)

        ctx = run.scheduler.make_context('scheduler', [], self.ctx)
        scheduler = run.scheduler.invoke(ctx)
        self.xmlrpc_thread = utils.run_in_thread(scheduler.xmlrpc_run)
        self.scheduler_thread = utils.run_in_thread(scheduler.run)

        time.sleep(1)

    @classmethod
    def tearDownClass(self):
        for each in self.ctx.obj.instances:
            each.quit()
        self.xmlrpc_thread.join()
        self.scheduler_thread.join()
        time.sleep(1)

        assert not utils.check_port_open(5000)
        assert not utils.check_port_open(23333)
        assert not utils.check_port_open(24444)
        assert not utils.check_port_open(25555)

        shutil.rmtree('./data/tests', ignore_errors=True)

    def test_10_send_message(self):
        ctx = run.send_message.make_context('send_message', [
            'test_project', 'test_message'
        ], self.ctx)
        self.assertTrue(run.send_message.invoke(ctx))
        while True:
            task = self.ctx.obj.scheduler2fetcher.get(timeout=1)
            if task['url'] == 'data:,on_message':
                break
        self.assertEqual(task['process']['callback'], '_on_message')

