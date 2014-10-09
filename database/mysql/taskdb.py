#!/usr/bin/envutils
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-17 18:53:01


import re
import time
import json
import mysql.connector

from database.base.taskdb import TaskDB as BaseTaskDB
from database.basedb import BaseDB


class TaskDB(BaseTaskDB, BaseDB):
    __tablename__ = ''
    def __init__(self, host='localhost', port=3306, database='taskdb',
            user='root', passwd=None):
        self.conn = mysql.connector.connect(user=user, password=passwd,
                host=host, port=port, autocommit=True)
        if database not in [x[0] for x in self._execute('show databases')]:
            self._execute('CREATE DATABASE %s' % self.escape(database))
        self.conn.database = database;
        self._list_project()

    @property
    def dbcur(self):
        return self.conn.cursor()

    def _tablename(self, project):
        if self.__tablename__:
            return '%s_%s' % (self.__tablename__, project)
        else:
            return project

    def _list_project(self):
        self.projects = set()
        if self.__tablename__:
            prefix = '%s_' % self.__tablename__
        else:
            prefix = ''
        for project, in self._execute('show tables;'):
            if project.startswith(prefix):
                project = project[len(prefix):]
                self.projects.add(project)

    def _create_project(self, project):
        assert re.match(r'^\w+$', project) is not None
        tablename = self._tablename(project)
        if tablename in [x[0] for x in self._execute('show tables')]:
            return
        self._execute('''CREATE TABLE %s (
            `taskid` varchar(64) PRIMARY KEY,
            `project` varchar(64),
            `url` varchar(1024),
            `status` int(1),
            `schedule` BLOB,
            `fetch` BLOB,
            `process` BLOB,
            `track` BLOB,
            `lastcrawltime` double(16, 4),
            `updatetime` double(16, 4)
            ) ENGINE=MyISAM CHARSET=utf8''' % self.escape(tablename))
        self._execute('''CREATE INDEX `status_index` ON %s (status)''' % self.escape(tablename))

    def _parse(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                if data[each]:
                    if type(data[each]) is bytearray:
                        data[each] = str(data[each])
                    data[each] = json.loads(unicode(data[each], 'utf8'))
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
        where = "`status` = %s" % self.placeholder

        if project:
            projects = [project, ]
        else:
            projects = self.projects

        for project in projects:
            tablename = self._tablename(project)
            for each in self._select2dic(tablename, what=fields, where=where, where_values=(status, )):
                yield self._parse(each)

    def get_task(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return None
        where = "`taskid` = %s" % self.placeholder
        if project not in self.projects:
            return None
        tablename = self._tablename(project)
        for each in self._select2dic(tablename, what=fields, where=where, where_values=(taskid, )):
            return self._parse(each)
        return None

    def status_count(self, project):
        result = dict()
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return result
        tablename = self._tablename(project)
        for status, count in self._execute("SELECT `status`, count(1) FROM %s GROUP BY `status`" % \
                self.escape(tablename)):
            result[status] = count
        return result

    def insert(self, project, taskid, obj={}):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            self._create_project(project)
            self._list_project()
        obj = dict(obj)
        obj['taskid'] = taskid
        obj['project'] = project
        obj['updatetime'] = time.time()
        tablename = self._tablename(project)
        self._insert(tablename, **self._stringify(obj))

    def update(self, project, taskid, obj={}, **kwargs):
        if project not in self.projects:
            raise LookupError
        tablename = self._tablename(project)
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        self._update(tablename, where="`taskid` = %s" % self.placeholder, where_values=(taskid, ),
                **self._stringify(obj))
