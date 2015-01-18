#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-04 23:25:10

import six
import time

from sqlalchemy import (create_engine, MetaData, Table, Column, Index,
                        Integer, String, Float, Text, sql, func)
from pyspider.libs import utils
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB
from .sqlalchemybase import result2dict

if six.PY3:
    where_type = utils.utf8
else:
    where_type = utils.text


class ProjectDB(BaseProjectDB):
    __tablename__ = 'projectdb'

    def __init__(self, url):
        self.table = Table(self.__tablename__, MetaData(),
                           Column('name', String(64)),
                           Column('group', String(64)),
                           Column('status', String(16)),
                           Column('script', Text),
                           Column('comments', String(1024)),
                           Column('rate', Float(11)),
                           Column('burst', Float(11)),
                           Column('updatetime', Float(32))
                           )
        self.engine = create_engine(url, convert_unicode=True)
        self.table.create(self.engine, checkfirst=True)

    @staticmethod
    def _parse(data):
        for key, value in list(six.iteritems(data)):
            if isinstance(value, six.binary_type):
                data[key] = utils.text(value)
        return data

    @staticmethod
    def _stringify(data):
        if six.PY3:
            for key, value in list(six.iteritems(data)):
                if isinstance(value, six.string_types):
                    data[key] = utils.utf8(value)
        return data

    def insert(self, name, obj={}):
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        return self.engine.execute(self.table.insert()
                                   .values(**self._stringify(obj)))

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        return self.engine.execute(self.table.update()
                                   .where(self.table.c.name == where_type(name))
                                   .values(**self._stringify(obj)))

    def get_all(self, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns)):
            yield self._parse(result2dict(columns, task))

    def get(self, name, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .where(self.table.c.name == where_type(name))
                                        .limit(1)
                                        .with_only_columns(columns)):
            return self._parse(result2dict(columns, task))

    def drop(self, name):
        return self.engine.execute(self.table.delete()
                                   .where(self.table.c.name == where_type(name)))

    def check_update(self, timestamp, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns)
                                        .where(self.table.c.updatetime >= timestamp)):
            yield self._parse(result2dict(columns, task))
