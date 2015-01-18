#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-04 22:33:43

import re
import six
import time
import json

from sqlalchemy import (create_engine, MetaData, Table, Column, Index,
                        Integer, String, Float, LargeBinary, sql, func)
from pyspider.libs import utils
from pyspider.database.base.taskdb import TaskDB as BaseTaskDB
from .sqlalchemybase import SplitTableMixin, result2dict

if six.PY3:
    where_type = utils.utf8
else:
    where_type = utils.text


class TaskDB(SplitTableMixin, BaseTaskDB):
    __tablename__ = ''

    def __init__(self, url):
        self.table = Table('__tablename__', MetaData(),
                           Column('taskid', String(64), primary_key=True, nullable=False),
                           Column('project', String(64)),
                           Column('url', String(1024)),
                           Column('status', Integer),
                           Column('schedule', LargeBinary),
                           Column('fetch', LargeBinary),
                           Column('process', LargeBinary),
                           Column('track', LargeBinary),
                           Column('lastcrawltime', Float(32)),
                           Column('updatetime', Float(32)),
                           )
        self.engine = create_engine(url, convert_unicode=True)

        self._list_project()

    def _create_project(self, project):
        assert re.match(r'^\w+$', project) is not None
        if project in self.projects:
            return
        self.table.name = self._tablename(project)
        Index('status_%s_index' % self.table.name, self.table.c.status)
        self.table.create(self.engine)
        self.table.indexes.clear()

    @staticmethod
    def _parse(data):
        for key, value in list(six.iteritems(data)):
            if isinstance(value, six.binary_type):
                data[key] = utils.text(value)
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                if data[each]:
                    if isinstance(data[each], bytearray):
                        data[each] = str(data[each])
                    data[each] = json.loads(data[each])
                else:
                    data[each] = {}
        return data

    @staticmethod
    def _stringify(data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                data[each] = json.dumps(data[each])
        if six.PY3:
            for key, value in list(six.iteritems(data)):
                if isinstance(value, six.string_types):
                    data[key] = utils.utf8(value)
        return data

    def load_tasks(self, status, project=None, fields=None):
        if project and project not in self.projects:
            return

        if project:
            projects = [project, ]
        else:
            projects = self.projects

        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for project in projects:
            self.table.name = self._tablename(project)
            for task in self.engine.execute(self.table.select()
                                            .with_only_columns(columns)
                                            .where(self.table.c.status == status)):
                yield self._parse(result2dict(columns, task))

    def get_task(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return None

        self.table.name = self._tablename(project)
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for each in self.engine.execute(self.table.select()
                                        .with_only_columns(columns)
                                        .limit(1)
                                        .where(self.table.c.taskid == where_type(taskid))):
            return self._parse(result2dict(columns, each))

    def status_count(self, project):
        result = dict()
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return result

        self.table.name = self._tablename(project)
        for status, count in self.engine.execute(
                self.table.select()
                .with_only_columns((self.table.c.status, func.count(1)))
                .group_by(self.table.c.status)):
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
        self.table.name = self._tablename(project)
        return self.engine.execute(self.table.insert()
                                   .values(**self._stringify(obj)))

    def update(self, project, taskid, obj={}, **kwargs):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            raise LookupError
        self.table.name = self._tablename(project)
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        return self.engine.execute(self.table.update()
                                   .where(self.table.c.taskid == where_type(taskid))
                                   .values(**self._stringify(obj)))
