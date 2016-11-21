#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-10 01:34:09

import os
import sys
import time
import click
import shutil
import inspect
import unittest2 as unittest

from pyspider import run
from pyspider.libs import utils
from pyspider.libs.utils import ObjectDict


class TestBench(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/bench', ignore_errors=True)
        os.makedirs('./data/bench')

    @classmethod
    def tearDownClass(self):
        shutil.rmtree('./data/bench', ignore_errors=True)

    def test_10_bench(self):
        ctx = run.cli.make_context('test', [
            '--queue-maxsize=0',
        ], None, obj=ObjectDict(testing_mode=True))
        base_ctx = run.cli.invoke(ctx)
        base_ctx.obj['testing_mode'] = False

        ctx = run.bench.make_context('bench', [
            '--total=500'
        ], base_ctx)
        bench = run.bench.invoke(ctx)

        stdout, stderr= capsys.readouterr()

        self.assertIn('Crawled', stderr)
        self.assertIn('Fetched', stderr)
        self.assertIn('Processed', stderr)
        self.assertIn('Saved', stderr)
