#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-05-16 21:01:52

import time
import redis
import json

from pyspider.database.base.taskdb import TaskDB as BaseTaskDB


class TaskDB(BaseTaskDB):
    __prefix__ = 'taskdb_'

    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        self._list_project()

    def _gen_key(self, project):
        return self.__prefix__ + project

    def _parse(self, data):
        return json.loads(data)

    def _stringify(self, data):
        return json.dumps(data)

    def _list_project(self):
        self.projects = set()
        for key in self.redis.scan_iter(self.__prefix__ + '*'):
            if not key.startswith(self.__prefix__):
                continue
            if '|s' in key:
                continue
            project = key[len(self.__prefix__):]
            self.projects.add(project)

    def load_tasks(self, status, project=None, fields=None):
        if project is None:
            self._list_project()
            project = self.projects
        elif not isinstance(project, list):
            project = [project, ]

        for p in project:
            project_key = self._gen_key(p)
            for taskid in self.redis.sscan_iter(project_key + '|s%d' % status):
                obj = self.redis.hget(project_key, taskid)
                if not obj:
                    self.redis.srem(project_key + '|s%d' % status, taskid)
                    continue
                obj = self._parse(obj)
                if fields:
                    for key in fields:
                        if key not in obj:
                            obj.pop(key)
                yield obj

    def get_task(self, project, taskid, fields=None):
        project_key = self._gen_key(project)
        obj = self.redis.hget(project_key, taskid)
        if not obj:
            return None
        obj = self._parse(obj)
        if fields:
            for key in fields:
                if key not in obj:
                    obj.pop(key)
        return obj

    def status_count(self, project):
        '''
        return a dict
        '''
        project_key = self._gen_key(project)
        pipe = self.redis.pipeline(transaction=False)
        for status in range(1, 5):
            pipe.scard(project_key + '|s%d' % status)

        result = {}
        for status, count in pipe.execute():
            result[status + 1] = count
        return result

    def insert(self, project, taskid, obj={}):
        obj = dict(obj)
        obj['taskid'] = taskid
        obj['project'] = project
        obj['updatetime'] = time.time()
        obj.setdefault('status', self.ACTIVE)
        project_key = self._gen_key(project)

        pipe = self.redis.pipeline(transaction=False)
        pipe.hset(project_key, taskid, self._stringify(obj))
        pipe.sadd(project_key + '|s%d' % obj['status'], taskid)
        pipe.execute()

    def update(self, project, taskid, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        project_key = self._gen_key(project)

        pipe = self.redis.pipeline(transaction=False)
        pipe.hset(project_key, taskid, self._stringify(obj))
        if 'status' in obj:
            for status in range(1, 5):
                if status == obj['status']:
                    pipe.sadd(project_key + '|s%d' % status, taskid)
                else:
                    pipe.srem(project_key + '|s%d' % status, taskid)
        pipe.execute()

    def drop(self, project):
        project_key = self._gen_key(project)
        with self.redis.pipeline() as pipe:
            pipe.delete(project_key)
            for status in range(1, 5):
                pipe.delete(project_key + '|s%d' % status)
