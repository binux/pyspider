#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-13 22:18:36

import json
import time
from pymongo import MongoClient
from database.base.resultdb import ResultDB as BaseResultDB

class ResultDB(BaseResultDB):
    collection_prefix = ''
    def __init__(self, url, database='resultdb'):
        self.conn = MongoClient(url)
        self.database = self.conn[database]
        self.projects = set()

        self._list_project()
        for project in self.projects:
            collection_name = self._collection_name(project)

    def _list_project(self):
        self.projects = set()
        if self.collection_prefix:
            prefix = "%s." % self.collection_prefix
        else:
            prefix = ''
        for each in self.database.collection_names():
            if each.startswith('system.'):
                continue
            if each.startswith(prefix):
                self.projects.add(each[len(prefix):])

    def _collection_name(self, project):
        if self.collection_prefix:
            return "%s.%s" % (self.collection_prefix, project)
        else:
            return project

    def _parse(self, data):
        if 'result' in data:
            data['result'] = json.loads(data['result'])
        return data

    def _stringify(self, data):
        if 'result' in data:
            data['result'] = json.dumps(data['result'])
        return data

    def save(self, project, taskid, url, result):
        collection_name = self._collection_name(project)
        obj = {
                'taskid': taskid,
                'url': url,
                'result': result,
                'updatetime': time.time(),
                }
        return self.database[collection_name].update({'taskid': taskid}, {"$set": self._stringify(obj)}, upsert=True)

    def select(self, project, fields=None, offset=0, limit=0):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        for result in self.database[collection_name].find(fields=fields, skip=offset, limit=limit):
            yield self._parse(result)

    def count(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        return self.database[collection_name].count()

    def get(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        ret = self.database[collection_name].find_one({'taskid': taskid}, fields=fields)
        if not ret:
            return ret
        return self._parse(ret)

    def drop(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        self.database[collection_name].drop()
        self._list_project()
