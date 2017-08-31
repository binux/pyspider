#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-09 10:53:19

import os
import unittest2 as unittest
path = os.path

library_base_path = path.abspath(path.join(path.dirname(__file__), '..'))

logger_config_path = path.join(library_base_path, "pyspider/logging.conf")

all_suite = unittest.TestLoader().discover(os.path.dirname(__file__), "test_*.py")


