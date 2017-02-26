#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-11 23:54:50

import json
import time
from pymongo import MongoClient

from pyspider.database.base.taskdb import TaskDB as BaseTaskDB
from .mongodbbase import SplitTableMixin


class TaskDB(SplitTableMixin, BaseTaskDB):
    collection_prefix = ''

    def __init__(self, url, database='taskdb'):
        self.conn = MongoClient(url)
        self.conn.admin.command("ismaster")
        self.database = self.conn[database]
        self.projects = set()

        self._list_project()
        for project in self.projects:
            collection_name = self._collection_name(project)
            self.database[collection_name].ensure_index('status')
            self.database[collection_name].ensure_index('taskid')

    def _create_project(self, project):
        collection_name = self._collection_name(project)
        self.database[collection_name].ensure_index('status')
        self.database[collection_name].ensure_index('taskid')
        self._list_project()

    def _parse(self, data):
        if '_id' in data:
            del data['_id']
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                if data[each]:
                    if isinstance(data[each], bytearray):
                        data[each] = str(data[each])
                    data[each] = json.loads(data[each], encoding='utf8')
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
            for task in self.database[collection_name].find({'status': status}, fields):
                yield self._parse(task)

    def get_task(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        ret = self.database[collection_name].find_one({'taskid': taskid}, fields)
        if not ret:
            return ret
        return self._parse(ret)

    def status_count(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return {}
        collection_name = self._collection_name(project)
        ret = self.database[collection_name].aggregate([
            {'$group': {
                '_id': '$status',
                'total': {
                    '$sum': 1
                }
            }
            }])
        result = {}
        if isinstance(ret, dict):
            ret = ret.get('result', [])
        for each in ret:
            result[each['_id']] = each['total']
        return result

    def insert(self, project, taskid, obj={}):
        if project not in self.projects:
            self._create_project(project)
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
        return self.database[collection_name].update(
            {'taskid': taskid},
            {"$set": self._stringify(obj)},
            upsert=True
        )
