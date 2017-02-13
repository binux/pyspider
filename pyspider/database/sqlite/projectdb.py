#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-09 12:05:52

import time

from .sqlitebase import SQLiteMixin
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB
from pyspider.database.basedb import BaseDB


class ProjectDB(SQLiteMixin, BaseProjectDB, BaseDB):
    __tablename__ = 'projectdb'
    placeholder = '?'

    def __init__(self, path):
        self.path = path
        self.last_pid = 0
        self.conn = None
        self._execute('''CREATE TABLE IF NOT EXISTS `%s` (
                name PRIMARY KEY,
                `group`,
                status, script, comments,
                rate, burst, updatetime
                )''' % self.__tablename__)

    def insert(self, name, obj={}):
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        return self._insert(**obj)

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        ret = self._update(where="`name` = %s" % self.placeholder, where_values=(name, ), **obj)
        return ret.rowcount

    def get_all(self, fields=None):
        return self._select2dic(what=fields)

    def get(self, name, fields=None):
        where = "`name` = %s" % self.placeholder
        for each in self._select2dic(what=fields, where=where, where_values=(name, )):
            return each
        return None

    def check_update(self, timestamp, fields=None):
        where = "`updatetime` >= %f" % timestamp
        return self._select2dic(what=fields, where=where)

    def drop(self, name):
        where = "`name` = %s" % self.placeholder
        return self._delete(where=where, where_values=(name, ))
