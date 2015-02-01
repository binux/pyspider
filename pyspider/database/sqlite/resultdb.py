#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-13 17:08:43

import re
import time
import json

from .sqlitebase import SQLiteMixin, SplitTableMixin
from pyspider.database.base.resultdb import ResultDB as BaseResultDB
from pyspider.database.basedb import BaseDB


class ResultDB(SQLiteMixin, SplitTableMixin, BaseResultDB, BaseDB):
    __tablename__ = 'resultdb'
    placeholder = '?'

    def __init__(self, path):
        self.path = path
        self.last_pid = 0
        self.conn = None
        self._list_project()

    def _create_project(self, project):
        assert re.match(r'^\w+$', project) is not None
        tablename = self._tablename(project)
        self._execute('''CREATE TABLE IF NOT EXISTS `%s` (
                taskid PRIMARY KEY,
                url,
                result,
                updatetime
                )''' % tablename)

    def _parse(self, data):
        if 'result' in data:
            data['result'] = json.loads(data['result'])
        return data

    def _stringify(self, data):
        if 'result' in data:
            data['result'] = json.dumps(data['result'])
        return data

    def save(self, project, taskid, url, result):
        tablename = self._tablename(project)
        if project not in self.projects:
            self._create_project(project)
            self._list_project()
        obj = {
            'taskid': taskid,
            'url': url,
            'result': result,
            'updatetime': time.time(),
        }
        return self._replace(tablename, **self._stringify(obj))

    def select(self, project, fields=None, offset=0, limit=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        tablename = self._tablename(project)

        for task in self._select2dic(tablename, what=fields, order='updatetime DESC',
                                     offset=offset, limit=limit):
            yield self._parse(task)

    def count(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return 0
        tablename = self._tablename(project)
        for count, in self._execute("SELECT count(1) FROM %s" % self.escape(tablename)):
            return count

    def get(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        tablename = self._tablename(project)
        where = "`taskid` = %s" % self.placeholder
        for task in self._select2dic(tablename, what=fields,
                                     where=where, where_values=(taskid, )):
            return self._parse(task)
