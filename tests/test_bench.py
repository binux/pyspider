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

class TestBench(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        shutil.rmtree('./data/bench', ignore_errors=True)
        os.makedirs('./data/bench')

    @classmethod
    def tearDownClass(self):
        shutil.rmtree('./data/bench', ignore_errors=True)

    def test_10_bench(self):
        import subprocess
        #cmd = [sys.executable]
        cmd = ['coverage', 'run']
        p = subprocess.Popen(cmd+[
            inspect.getsourcefile(run),
            '--queue-maxsize=0',
            'bench',
            '--total=500'
        ], close_fds=True, stderr=subprocess.PIPE)

        stdout, stderr = p.communicate()
        stderr = utils.text(stderr)
        print(stderr)

        self.assertEqual(p.returncode, 0, stderr)
        self.assertIn('Crawled', stderr)
        self.assertIn('Fetched', stderr)
        self.assertIn('Processed', stderr)
        self.assertIn('Saved', stderr)
