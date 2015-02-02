#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-04 18:48:15

import re
import six
import time
import json

from sqlalchemy import (create_engine, MetaData, Table, Column,
                        String, Float, LargeBinary)
from pyspider.database.base.resultdb import ResultDB as BaseResultDB
from pyspider.libs import utils
from .sqlalchemybase import SplitTableMixin, result2dict

if six.PY3:
    where_type = utils.utf8
else:
    where_type = utils.text


class ResultDB(SplitTableMixin, BaseResultDB):
    __tablename__ = ''

    def __init__(self, url):
        self.table = Table('__tablename__', MetaData(),
                           Column('taskid', String(64), primary_key=True, nullable=False),
                           Column('url', String(1024)),
                           Column('result', LargeBinary),
                           Column('updatetime', Float(32))
                           )
        self.engine = create_engine(url, convert_unicode=True)

        self._list_project()

    def _create_project(self, project):
        assert re.match(r'^\w+$', project) is not None
        if project in self.projects:
            return
        self.table.name = self._tablename(project)
        self.table.create(self.engine)

    @staticmethod
    def _parse(data):
        for key, value in list(six.iteritems(data)):
            if isinstance(value, six.binary_type):
                data[key] = utils.text(value)
        if 'result' in data:
            if isinstance(data['result'], bytearray):
                data['result'] = str(data['result'])
            data['result'] = json.loads(data['result'])
        return data

    @staticmethod
    def _stringify(data):
        if 'result' in data:
            data['result'] = json.dumps(data['result'])
        if six.PY3:
            for key, value in list(six.iteritems(data)):
                if isinstance(value, six.string_types):
                    data[key] = utils.utf8(value)
        return data

    def save(self, project, taskid, url, result):
        if project not in self.projects:
            self._create_project(project)
            self._list_project()
        self.table.name = self._tablename(project)
        obj = {
            'taskid': taskid,
            'url': url,
            'result': result,
            'updatetime': time.time(),
        }
        if self.get(project, taskid, ('taskid', )):
            del obj['taskid']
            return self.engine.execute(self.table.update()
                                       .where(self.table.c.taskid == where_type(taskid))
                                       .values(**self._stringify(obj)))
        else:
            return self.engine.execute(self.table.insert()
                                       .values(**self._stringify(obj)))

    def select(self, project, fields=None, offset=0, limit=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        self.table.name = self._tablename(project)

        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns=columns)
                                        .order_by(self.table.c.updatetime.desc())
                                        .offset(offset).limit(limit)
                                        .execution_options(autocommit=True)):
            yield self._parse(result2dict(columns, task))

    def count(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return 0
        self.table.name = self._tablename(project)

        for count, in self.engine.execute(self.table.count()):
            return count

    def get(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        self.table.name = self._tablename(project)

        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns=columns)
                                        .where(self.table.c.taskid == where_type(taskid))
                                        .limit(1)):
            return self._parse(result2dict(columns, task))
