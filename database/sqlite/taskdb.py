#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 10:25:34

import os
import re
import time
import json
import thread
import sqlite3
from database.base.taskdb import TaskDB as BaseTaskDB
from database.basedb import BaseDB


class TaskDB(BaseTaskDB, BaseDB):
    __tablename__ = 'taskdb'
    placeholder = '?'

    def __init__(self, path):
        self.path = path
        self.last_pid = 0
        self.conn = None
        self._list_project()

    @property
    def dbcur(self):
        pid = thread.get_ident()
        if not (self.conn and pid == self.last_pid):
            self.last_pid = pid
            self.conn = sqlite3.connect(self.path, isolation_level=None)
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
                if data[each]:
                    data[each] = json.loads(data[each])
                else:
                    data[each] = {}
        return data

    def _stringify(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                data[each] = json.dumps(data[each])
        return data

    def load_tasks(self, status, project=None, fields=None):
        if project and project not in self.projects:
            return
        where = "status = %d" % status

        if project:
            projects = [project, ]
        else:
            projects = self.projects

        for project in projects:
            tablename = '%s_%s' % (self.__tablename__, project)
            for each in self._select2dic(tablename, what=fields, where=where):
                yield self._parse(each)

    def get_task(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return None
        where = "`taskid` = %s" % self.placeholder
        if project not in self.projects:
            return None
        tablename = '%s_%s' % (self.__tablename__, project)
        for each in self._select2dic(tablename, what=fields, where=where, where_values=(taskid, )):
            return self._parse(each)
        return None

    def status_count(self, project):
        '''
        return a dict
        '''
        result = dict()
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return result
        tablename = '%s_%s' % (self.__tablename__, project)
        for status, count in self._execute("SELECT `status`, count(1) FROM %s GROUP BY `status`" % \
                self.escape(tablename)):
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
        self._update(tablename, where="`taskid` = %s" % self.placeholder, where_values=(taskid, ),
                **self._stringify(obj))
