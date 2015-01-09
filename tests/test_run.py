#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-21 22:32:35

import os
import six
import json
import shutil
import unittest2 as unittest

from pyspider import run
from pyspider.libs.utils import ObjectDict


class TestRun(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/tests', ignore_errors=True)
        os.makedirs('./data/tests')

    @classmethod
    def tearDownClass(self):
        shutil.rmtree('./data/tests', ignore_errors=True)

    def test_10_cli(self):
        ctx = run.cli.make_context('test', [], None, obj=ObjectDict(testing_mode=True))
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
                                   None, obj=ObjectDict(testing_mode=True))
        ctx = run.cli.invoke(ctx)
        self.assertEqual(ctx.obj.debug, True)

        import mysql.connector
        with self.assertRaises(mysql.connector.InterfaceError):
            ctx.obj.taskdb

        with self.assertRaisesRegexp(Exception, 'Connection refused'):
            ctx.obj.newtask_queue

    def test_30_cli_command_line(self):
        ctx = run.cli.make_context(
            'test',
            ['--projectdb', 'mongodb+projectdb://localhost:23456/projectdb'],
            None,
            obj=ObjectDict(testing_mode=True)
        )
        ctx = run.cli.invoke(ctx)

        from pymongo.errors import ConnectionFailure
        with self.assertRaises(ConnectionFailure):
            ctx.obj.projectdb

    def test_40_cli_env(self):
        try:
            os.environ['RESULTDB'] = 'sqlite+resultdb://'
            ctx = run.cli.make_context('test', [], None,
                                       obj=ObjectDict(testing_mode=True))
            ctx = run.cli.invoke(ctx)

            from pyspider.database.sqlite import resultdb
            self.assertIsInstance(ctx.obj.resultdb, resultdb.ResultDB)
        finally:
            del os.environ['RESULTDB']

    @unittest.skipIf(os.environ.get('IGNORE_RABBITMQ'), 'no rabbitmq server for test.')
    def test_50_docker_rabbitmq(self):
        try:
            os.environ['RABBITMQ_NAME'] = 'rabbitmq'
            os.environ['RABBITMQ_PORT_5672_TCP_ADDR'] = 'localhost'
            os.environ['RABBITMQ_PORT_5672_TCP_PORT'] = '5672'
            ctx = run.cli.make_context('test', [], None,
                                       obj=ObjectDict(testing_mode=True))
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

    @unittest.skipIf(os.environ.get('IGNORE_MONGODB'), 'no mongodb server for test.')
    def test_60_docker_mongodb(self):
        try:
            os.environ['MONGODB_NAME'] = 'mongodb'
            os.environ['MONGODB_PORT_27017_TCP_ADDR'] = 'localhost'
            os.environ['MONGODB_PORT_27017_TCP_PORT'] = '27017'
            ctx = run.cli.make_context('test', [], None,
                                       obj=ObjectDict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            ctx.obj.resultdb
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['MONGODB_NAME']
            del os.environ['MONGODB_PORT_27017_TCP_ADDR']
            del os.environ['MONGODB_PORT_27017_TCP_PORT']

    @unittest.skipIf(os.environ.get('IGNORE_MYSQL'), 'no mysql server for test.')
    def test_70_docker_mysql(self):
        try:
            os.environ['MYSQL_NAME'] = 'mysql'
            os.environ['MYSQL_PORT_3306_TCP_ADDR'] = 'localhost'
            os.environ['MYSQL_PORT_3306_TCP_PORT'] = '3306'
            ctx = run.cli.make_context('test', [], None,
                                       obj=ObjectDict(testing_mode=True))
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
            os.environ['PHANTOMJS_PORT'] = 'tpc://binux:25678'
            ctx = run.cli.make_context('test', [], None,
                                       obj=ObjectDict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            self.assertEqual(ctx.obj.phantomjs_proxy, 'binux:25678')
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['PHANTOMJS_NAME']
            del os.environ['PHANTOMJS_PORT']

    def test_90_docker_scheduler(self):
        try:
            os.environ['SCHEDULER_NAME'] = 'scheduler'
            os.environ['SCHEDULER_PORT_23333_TCP'] = 'tpc://binux:25678'
            ctx = run.cli.make_context('test', [], None,
                                       obj=ObjectDict(testing_mode=True))
            ctx = run.cli.invoke(ctx)
            webui = run.cli.get_command(ctx, 'webui')
            webui_ctx = webui.make_context('webui', [], ctx)
            app = webui.invoke(webui_ctx)
            rpc = app.config['scheduler_rpc']
            self.assertEqual(rpc._ServerProxy__host, 'binux:25678')
        except Exception as e:
            self.assertIsNone(e)
        finally:
            del os.environ['SCHEDULER_NAME']
            del os.environ['SCHEDULER_PORT_23333_TCP']

    def test_a10_all(self):
        pass
