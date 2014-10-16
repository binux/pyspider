#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-16 23:55:41

import unittest2 as unittest

suite = unittest.TestLoader().discover('test', "test_*.py")
unittest.TextTestRunner(verbosity=1).run(suite)
