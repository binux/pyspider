#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-11 23:54:50

import re
import json
import time
from pymongo import MongoClient

from database.base.taskdb import TaskDB as BaseTaskDB


class TaskDB(BaseTaskDB):
    collection_prefix = ''
    def __init__(self, url, database='taskdb'):
        self.conn = MongoClient(url)
        self.database = self.conn[database]
        self._list_project()

    def _list_project(self):
        self.projects = set()
        if self.collection_prefix:
            prefix = "%s." % self.collection_prefix
        else:
            prefix = ''
        for each in self.database.collection_names():
            if each.startswith(prefix):
                self.projects.add(each[len(prefix):])

    def _collection_name(self, project):
        if self.collection_prefix:
            return "%s.%s" % (self.collection_prefix, project)
        else:
            return project

    def _parse(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                if data[each]:
                    if type(data[each]) is bytearray:
                        data[each] = str(data[each])
                    data[each] = json.loads(data[each], 'utf8')
                else:
                    data[each] = {}
        return data

    def _stringify(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                data[each] = json.dumps(data[each])
        return data

    def load_tasks(self, status, project=None, fields=None):
        if not project:
            self._list_project()

        if project:
            projects = [project, ]
        else:
            projects = self.projects

        for project in projects:
            collection_name = self._collection_name(project)
            for task in self.database[collection_name].find({'status': status}, fields=fields):
                yield self._parse(task)

    def get_task(self, project, taskid, fields=None):
        collection_name = self._collection_name(project)
        ret = self.database[collection_name].find_one({'taskid': taskid}, fields=fields)
        if not ret:
            return ret
        return self._parse(ret)

    def status_count(self, project):
        collection_name = self._collection_name(project)
        ret = self.database[collection_name].aggregate( [
           { '$group': {
               '_id': '$status',
               'total': {
                   '$sum': 1
                   }
               }
            } ] )
        result = {}
        if ret.get('result'):
            for each in ret['result']:
                result[each['_id']] = each['total']
            return result
        return result

    def insert(self, project, taskid, obj={}):
        obj = dict(obj)
        obj['taskid'] = taskid
        obj['project'] = project
        obj['updatetime'] = time.time()
        return self.update(project, taskid, obj=obj)

    def update(self, project, taskid, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        collection_name = self._collection_name(project)
        return self.database[collection_name].update({'taskid': taskid}, {"$set": self._stringify(obj)}, upsert=True)
