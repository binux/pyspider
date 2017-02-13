#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-04 23:25:10

import six
import time
import sqlalchemy.exc

from sqlalchemy import create_engine, MetaData, Table, Column, String, Float, Text
from sqlalchemy.engine.url import make_url
from pyspider.libs import utils
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB
from .sqlalchemybase import result2dict


class ProjectDB(BaseProjectDB):
    __tablename__ = 'projectdb'

    def __init__(self, url):
        self.table = Table(self.__tablename__, MetaData(),
                           Column('name', String(64), primary_key=True),
                           Column('group', String(64)),
                           Column('status', String(16)),
                           Column('script', Text),
                           Column('comments', String(1024)),
                           Column('rate', Float(11)),
                           Column('burst', Float(11)),
                           Column('updatetime', Float(32)),
                           mysql_engine='InnoDB',
                           mysql_charset='utf8'
                           )

        self.url = make_url(url)
        if self.url.database:
            database = self.url.database
            self.url.database = None
            try:
                engine = create_engine(self.url, convert_unicode=True, pool_recycle=3600)
                conn = engine.connect()
                conn.execute("commit")
                conn.execute("CREATE DATABASE %s" % database)
            except sqlalchemy.exc.SQLAlchemyError:
                pass
            self.url.database = database
        self.engine = create_engine(url, convert_unicode=True, pool_recycle=3600)
        self.table.create(self.engine, checkfirst=True)

    @staticmethod
    def _parse(data):
        return data

    @staticmethod
    def _stringify(data):
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
                                   .where(self.table.c.name == name)
                                   .values(**self._stringify(obj)))

    def get_all(self, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns)):
            yield self._parse(result2dict(columns, task))

    def get(self, name, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .where(self.table.c.name == name)
                                        .limit(1)
                                        .with_only_columns(columns)):
            return self._parse(result2dict(columns, task))

    def drop(self, name):
        return self.engine.execute(self.table.delete()
                                   .where(self.table.c.name == name))

    def check_update(self, timestamp, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns)
                                        .where(self.table.c.updatetime >= timestamp)):
            yield self._parse(result2dict(columns, task))
