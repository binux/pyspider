#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-16 23:55:41

import sys
import unittest2 as unittest

if __name__ == '__main__':
    glob = "test_*.py"
    if len(sys.argv) > 1:
        glob = sys.argv[1]

    suite = unittest.TestLoader().discover('tests', glob)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if result.errors or result.failures:
        sys.exit(1)
    sys.exit(0)
