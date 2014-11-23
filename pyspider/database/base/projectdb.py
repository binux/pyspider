#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-09 11:28:52

import re

{
    'project': {
        'name': str,
        'group': str,
        'status': str,
        'script': str,
        # 'config': str,
        'comments': str,
        # 'priority': int,
        'rate': int,
        'burst': int,
        'updatetime': int,
    }
}


class ProjectDB(object):
    status_str = [
        'TODO',
        'STOP',
        'CHECKING',
        'DEBUG',
        'RUNNING',
    ]

    def insert(self, name, obj={}):
        raise NotImplementedError

    def update(self, name, obj={}, **kwargs):
        raise NotImplementedError

    def get_all(self, fields=None):
        raise NotImplementedError

    def get(self, name, fields):
        raise NotImplementedError

    def drop(self, name):
        raise NotImplementedError

    def check_update(self, timestamp, fields=None):
        raise NotImplementedError

    def split_group(self, group, lower=True):
        return re.split("\W+", (group or '').lower())
