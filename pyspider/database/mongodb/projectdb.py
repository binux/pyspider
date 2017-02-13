#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-12 12:22:42

import time
from pymongo import MongoClient

from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB


class ProjectDB(BaseProjectDB):
    __collection_name__ = 'projectdb'

    def __init__(self, url, database='projectdb'):
        self.conn = MongoClient(url)
        self.conn.admin.command("ismaster")
        self.database = self.conn[database]
        self.collection = self.database[self.__collection_name__]

        self.collection.ensure_index('name', unique=True)

    def _default_fields(self, each):
        if each is None:
            return each
        each.setdefault('group', None)
        each.setdefault('status', 'TODO')
        each.setdefault('script', '')
        each.setdefault('comments', None)
        each.setdefault('rate', 0)
        each.setdefault('burst', 0)
        each.setdefault('updatetime', 0)
        return each

    def insert(self, name, obj={}):
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        return self.collection.update({'name': name}, {'$set': obj}, upsert=True)

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        return self.collection.update({'name': name}, {'$set': obj})

    def get_all(self, fields=None):
        for each in self.collection.find({}, fields):
            if each and '_id' in each:
                del each['_id']
            yield self._default_fields(each)

    def get(self, name, fields=None):
        each = self.collection.find_one({'name': name}, fields)
        if each and '_id' in each:
            del each['_id']
        return self._default_fields(each)

    def check_update(self, timestamp, fields=None):
        for project in self.get_all(fields=('updatetime', 'name')):
            if project['updatetime'] > timestamp:
                project = self.get(project['name'], fields)
                yield self._default_fields(project)

    def drop(self, name):
        return self.collection.remove({'name': name})
