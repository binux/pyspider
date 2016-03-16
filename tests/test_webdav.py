#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-06-03 21:15

import os
import six
import time
import shutil
import inspect
import unittest2 as unittest

from six import BytesIO
from pyspider import run
from pyspider.libs import utils
from tests import data_sample_handler, data_handler

@unittest.skipIf(six.PY3, 'webdav not support python3')
class TestWebDav(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        import easywebdav

        shutil.rmtree('./data/tests', ignore_errors=True)
        os.makedirs('./data/tests')

        ctx = run.cli.make_context('test', [
            '--taskdb', 'sqlite+taskdb:///data/tests/task.db',
            '--projectdb', 'sqlite+projectdb:///data/tests/projectdb.db',
            '--resultdb', 'sqlite+resultdb:///data/tests/resultdb.db',
        ], None, obj=utils.ObjectDict(testing_mode=True))
        self.ctx = run.cli.invoke(ctx)

        ctx = run.webui.make_context('webui', [
            '--username', 'binux',
            '--password', '4321',
        ], self.ctx)
        self.app = run.webui.invoke(ctx)
        self.app_thread = utils.run_in_thread(self.app.run)
        time.sleep(5)

        self.webdav = easywebdav.connect('localhost', port=5000, path='dav')
        self.webdav_up = easywebdav.connect('localhost', port=5000, path='dav',
                                            username='binux', password='4321')

    @classmethod
    def tearDownClass(self):
        for each in self.ctx.obj.instances:
            each.quit()
        self.app_thread.join()
        time.sleep(1)

        assert not utils.check_port_open(5000)
        assert not utils.check_port_open(23333)
        assert not utils.check_port_open(24444)
        assert not utils.check_port_open(25555)
        assert not utils.check_port_open(14887)

        shutil.rmtree('./data/tests', ignore_errors=True)

    def test_10_ls(self):
        self.assertEqual(len(self.webdav.ls()), 1)

    def test_20_create_error(self):
        import easywebdav
        with self.assertRaises(easywebdav.OperationFailed):
            self.webdav.upload(inspect.getsourcefile(data_sample_handler),
                               'bad_file_name')
        with self.assertRaises(easywebdav.OperationFailed):
            self.webdav.upload(inspect.getsourcefile(data_sample_handler),
                               'bad.file.name')

    def test_30_create_ok(self):
        self.webdav.upload(inspect.getsourcefile(data_handler), 'handler.py')
        self.webdav.upload(inspect.getsourcefile(data_sample_handler), 'sample_handler.py')
        self.assertEqual(len(self.webdav.ls()), 3)

    def test_40_get_404(self):
        io = BytesIO()
        import easywebdav
        with self.assertRaises(easywebdav.OperationFailed):
            self.webdav.download('not_exitst', io)
        io.close()

    def test_50_get(self):
        io = BytesIO()
        self.webdav.download('handler.py', io)
        self.assertEqual(inspect.getsource(data_handler), io.getvalue())
        io.close()

        io = BytesIO()
        self.webdav.download('sample_handler.py', io)
        self.assertEqual(inspect.getsource(data_sample_handler), io.getvalue())
        io.close()

    def test_60_edit(self):
        self.webdav.upload(inspect.getsourcefile(data_handler), 'sample_handler.py')

    def test_70_get(self):
        io = BytesIO()
        self.webdav.download('sample_handler.py', io)
        self.assertEqual(inspect.getsource(data_handler), io.getvalue())
        io.close()

    def test_80_password(self):
        import requests
        rv = requests.post('http://localhost:5000/update', data={
            'name': 'group',
            'value': 'lock',
            'pk': 'sample_handler',
        })
        self.assertEqual(rv.status_code, 200)

        import easywebdav
        with self.assertRaises(easywebdav.OperationFailed):
            self.webdav.upload(inspect.getsourcefile(data_sample_handler), 'sample_handler.py')
        self.webdav_up.upload(inspect.getsourcefile(data_sample_handler), 'sample_handler.py')

