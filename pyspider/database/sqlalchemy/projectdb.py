#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-04 23:25:10

import re
import time
import json

from sqlalchemy import (create_engine, MetaData, Table, Column, Index,
                        Integer, String, Float, Text, sql, func)
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB
from .sqlalchemybase import result2dict

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
                           Column('updatetime', Float(16))
                           )
        self.engine = create_engine(url)
        self.table.create(self.engine, checkfirst=True)

    def insert(self, name, obj={}):
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        return self.engine.execute(self.table.insert()
                                   .values(**obj))

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        return self.engine.execute(self.table.update()
                                   .where(self.table.c.name == name)
                                   .values(**obj))

    def get_all(self, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns)):
            yield result2dict(columns, task)

    def get(self, name, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .where(self.table.c.name == name)
                                        .limit(1)
                                        .with_only_columns(columns)):
            return result2dict(columns, task)

    def drop(self, name):
        return self.engine.execute(self.table.delete()
                                   .where(self.table.c.name == name))

    def check_update(self, timestamp, fields=None):
        columns = [getattr(self.table.c, f, f) for f in fields] if fields else self.table.c
        for task in self.engine.execute(self.table.select()
                                        .with_only_columns(columns)
                                        .where(self.table.c.updatetime >= timestamp)):
            yield result2dict(columns, task)
