#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-11-10 01:31:54

import sys
from unittest.mock import MagicMock
from recommonmark.parser import CommonMarkParser

class Mock(MagicMock):
    @classmethod
    def __getattr__(cls, name):
            return Mock()

MOCK_MODULES = ['pycurl', 'lxml', 'psycopg2']
sys.modules.update((mod_name, Mock()) for mod_name in MOCK_MODULES)

source_parsers = {
        '.md': CommonMarkParser,
}

source_suffix = ['.rst', '.md']
