#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-05-16 21:01:52

import six
import time
import json
import redis
import logging
import itertools

from pyspider.libs import utils
from pyspider.database.base.taskdb import TaskDB as BaseTaskDB


class TaskDB(BaseTaskDB):
    UPDATE_PROJECTS_TIME = 10 * 60
    __prefix__ = 'taskdb_'

    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)
        try:
            self.redis.scan(count=1)
            self.scan_available = True
        except Exception as e:
            logging.debug("redis_scan disabled: %r", e)
            self.scan_available = False

    def _gen_key(self, project, taskid):
        return "%s%s_%s" % (self.__prefix__, project, taskid)

    def _gen_status_key(self, project, status):
        return '%s%s_status_%d' % (self.__prefix__, project, status)

    def _parse(self, data):
        if six.PY3:
            result = {}
            for key, value in data.items():
                if isinstance(value, bytes):
                    value = utils.text(value)
                result[utils.text(key)] = value
            data = result

        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                if data[each]:
                    data[each] = json.loads(data[each])
                else:
                    data[each] = {}
        if 'status' in data:
            data['status'] = int(data['status'])
        if 'lastcrawltime' in data:
            data['lastcrawltime'] = float(data['lastcrawltime'] or 0)
        if 'updatetime' in data:
            data['updatetime'] = float(data['updatetime'] or 0)
        return data

    def _stringify(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                data[each] = json.dumps(data[each])
        return data

    @property
    def projects(self):
        if time.time() - getattr(self, '_last_update_projects', 0) \
                > self.UPDATE_PROJECTS_TIME:
            self._projects = set(utils.text(x) for x in self.redis.smembers(
                self.__prefix__ + 'projects'))
        return self._projects

    def load_tasks(self, status, project=None, fields=None):
        if project is None:
            project = self.projects
        elif not isinstance(project, list):
            project = [project, ]

        if self.scan_available:
            scan_method = self.redis.sscan_iter
        else:
            scan_method = self.redis.smembers

        if fields:
            def get_method(key):
                obj = self.redis.hmget(key, fields)
                if all(x is None for x in obj):
                    return None
                return dict(zip(fields, obj))
        else:
            get_method = self.redis.hgetall

        for p in project:
            status_key = self._gen_status_key(p, status)
            for taskid in scan_method(status_key):
                obj = get_method(self._gen_key(p, utils.text(taskid)))
                if not obj:
                    #self.redis.srem(status_key, taskid)
                    continue
                else:
                    yield self._parse(obj)

    def get_task(self, project, taskid, fields=None):
        if fields:
            obj = self.redis.hmget(self._gen_key(project, taskid), fields)
            if all(x is None for x in obj):
                return None
            obj = dict(zip(fields, obj))
        else:
            obj = self.redis.hgetall(self._gen_key(project, taskid))

        if not obj:
            return None
        return self._parse(obj)

    def status_count(self, project):
        '''
        return a dict
        '''
        pipe = self.redis.pipeline(transaction=False)
        for status in range(1, 5):
            pipe.scard(self._gen_status_key(project, status))
        ret = pipe.execute()

        result = {}
        for status, count in enumerate(ret):
            if count > 0:
                result[status + 1] = count
        return result

    def insert(self, project, taskid, obj={}):
        obj = dict(obj)
        obj['taskid'] = taskid
        obj['project'] = project
        obj['updatetime'] = time.time()
        obj.setdefault('status', self.ACTIVE)

        task_key = self._gen_key(project, taskid)

        pipe = self.redis.pipeline(transaction=False)
        if project not in self.projects:
            pipe.sadd(self.__prefix__ + 'projects', project)
        pipe.hmset(task_key, self._stringify(obj))
        pipe.sadd(self._gen_status_key(project, obj['status']), taskid)
        pipe.execute()

    def update(self, project, taskid, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()

        pipe = self.redis.pipeline(transaction=False)
        pipe.hmset(self._gen_key(project, taskid), self._stringify(obj))
        if 'status' in obj:
            for status in range(1, 5):
                if status == obj['status']:
                    pipe.sadd(self._gen_status_key(project, status), taskid)
                else:
                    pipe.srem(self._gen_status_key(project, status), taskid)
        pipe.execute()

    def drop(self, project):
        self.redis.srem(self.__prefix__ + 'projects', project)

        if self.scan_available:
            scan_method = self.redis.scan_iter
        else:
            scan_method = self.redis.keys

        for each in itertools.tee(scan_method("%s%s_*" % (self.__prefix__, project)), 100):
            each = list(each)
            if each:
                self.redis.delete(*each)
