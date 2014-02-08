#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 10:25:34

import re
import time
import json
import sqlite3
from database.base.taskdb import TaskDB as BaseTaskDB
from basedb import BaseDB


class TaskDB(BaseTaskDB, BaseDB):
    __tablename__ = 'taskdb'
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self._list_project()

    @property
    def dbcur(self):
        return self.conn.cursor()

    def _list_project(self):
        self.projects = set()
        prefix = '%s_' % self.__tablename__
        for project, in self._select('sqlite_master', what='name',
                where='type = "table"'):
            if project.startswith(prefix):
                project = project[len(prefix):]
                self.projects.add(project)

    def _create_project(self, project):
        assert re.match(r'^\w+$', project) is not None
        tablename = '%s_%s' % (self.__tablename__, project)
        self._execute('''CREATE TABLE IF NOT EXISTS `%s` (
                taskid PRIMARY KEY,
                project,
                url, status,
                schedule, fetch, process, track,
                lastcrawltime, updatetime
                )''' % tablename)

    def _parse(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                data[each] = json.loads(data[each])
        return data

    def _stringify(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                data[each] = json.dumps(data[each])
        return data

    def load_tasks(self, status, project=None, fields=None):
        what = ','.join(fields) if fields else '*'
        where = "status = %d" % status
        if project:
            tablename = '%s_%s' % (self.__tablename__, project)
            for each in self._select2dic(tablename, what=what, where=where):
                yield self._parse(each)
        else:
            for project in self.projects:
                tablename = '%s_%s' % (self.__tablename__, project)
                for each in self._select2dic(tablename, what=what, where=where):
                    yield self._parse(each)

    def get_task(self, project, taskid, fields=None):
        what = ','.join(fields) if fields else '*'
        where = "taskid = '%s'" % taskid
        if project not in self.projects:
            return None
        tablename = '%s_%s' % (self.__tablename__, project)
        for each in self._select2dic(tablename, what=what, where=where):
            return self._parse(each)
        return None

    def status_count(self, project):
        '''
        return a dict
        '''
        result = dict()
        if project not in self.projects:
            return result
        tablename = '%s_%s' % (self.__tablename__, project)
        for status, count in self._execute("SELECT status, count(1) FROM '%s' GROUP BY status" % tablename).fetchall():
            result[status] = count
        return result

    def insert(self, project, taskid, obj={}):
        if project not in self.projects:
            self._create_project(project)
            self._list_project()
        obj = dict(obj)
        obj['taskid'] = taskid
        obj['project'] = project
        obj['updatetime'] = time.time()
        tablename = '%s_%s' % (self.__tablename__, project)
        self._insert(tablename, **self._stringify(obj))
        
    def update(self, project, taskid, obj={}, **kwargs):
        if project not in self.projects:
            raise LookupError
        tablename = '%s_%s' % (self.__tablename__, project)
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        self._update(tablename, where="taskid = '%s'" % taskid, **self._stringify(obj))
