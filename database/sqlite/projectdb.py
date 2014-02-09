#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-09 12:05:52

import re
import time
import sqlite3
from database.base.projectdb import ProjectDB as BaseProjectDB
from basedb import BaseDB


class ProjectDB(BaseProjectDB, BaseDB):
    __tablename__ = 'projectdb'
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self._execute('''CREATE TABLE IF NOT EXISTS `%s` (
                name PRIMARY KEY,
                `group`,
                status, script, comments,
                rate, burst, updatetime
                )''' % self.__tablename__)

    @property
    def dbcur(self):
        return self.conn.cursor()

    def insert(self, name, obj={}):
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        return self._insert(self.__tablename__, **obj)

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        self._update(self.__tablename__, where="name = '%s'" % name, **obj)

    def get_all(self, fields=None):
        what = ','.join(('`%s`' % x for x in fields)) if fields else '*'
        return self._select2dic(self.__tablename__, what=what)

    def get(self, name, fields=None):
        what = ','.join(('`%s`' % x for x in fields)) if fields else '*'
        where = "name = '%s'" % name
        for each in self._select2dic(self.__tablename__, what=what, where=where):
            return each
        return None

    def check_update(self, timestamp, fields=None):
        what = ','.join(('`%s`' % x for x in fields)) if fields else '*'
        where = "updatetime >= %f" % timestamp
        return self._select2dic(self.__tablename__, what=what, where=where)
