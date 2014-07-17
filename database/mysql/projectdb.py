#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-17 21:06:43

import re
import time
import json
import mysql.connector

from database.base.projectdb import ProjectDB as BaseProjectDB
from basedb import BaseDB

class ProjectDB(BaseProjectDB, BaseDB):
    __tablename__ = 'projectdb'
    def __init__(self, host='localhost', port=3306, database='projectdb',
            user='root', passwd=None):
        self.conn = mysql.connector.connect(user=user, password=passwd,
                host=host, port=port)
        if database not in [x[0] for x in self._execute('show databases')]:
            self._execute('CREATE DATABASE `%s`' % database)
        self.conn.database = database;

        self._execute('''CREATE TABLE IF NOT EXISTS `%s` (
            `name` varchar(64) PRIMARY KEY,
            `group` varchar(64),
            `status` varchar(16),
            `script` TEXT,
            `comments` varchar(1024),
            `rate` float(11, 4),
            `burst` float(11, 4),
            `updatetime` double(16, 4)
            ) ENGINE=MyISAM CHARSET=utf8''' % self.__tablename__)

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
        ret = self._update(self.__tablename__, where="name = %s" % json.dumps(name), **obj)
        return ret.rowcount

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
