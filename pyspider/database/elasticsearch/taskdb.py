#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2016-01-20 20:20:55


import time
import json

import elasticsearch.helpers
from elasticsearch import Elasticsearch
from pyspider.database.base.taskdb import TaskDB as BaseTaskDB


class TaskDB(BaseTaskDB):
    __type__ = 'task'

    def __init__(self, hosts, index='pyspider'):
        self.index = index
        self._changed = False
        self.es = Elasticsearch(hosts=hosts)

        self.es.indices.create(index=self.index, ignore=400)
        if not self.es.indices.get_mapping(index=self.index, doc_type=self.__type__):
            self.es.indices.put_mapping(index=self.index, doc_type=self.__type__, body={
                "_all": {"enabled": False},
                "properties": {
                    "project": {"type": "string", "index": "not_analyzed"},
                    "status": {"type": "byte"},
                }
            })

    def _parse(self, data):
        if not data:
            return data
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                if data[each]:
                    data[each] = json.loads(data[each])
                else:
                    data[each] = {}
        return data

    def _stringify(self, data):
        for each in ('schedule', 'fetch', 'process', 'track'):
            if each in data:
                data[each] = json.dumps(data[each])
        return data

    @property
    def projects(self):
        ret = self.es.search(index=self.index, doc_type=self.__type__,
                             body={"aggs": {"projects": {
                                 "terms": {"field": "project"}
                             }}}, _source=False)
        return [each['key'] for each in ret['aggregations']['projects'].get('buckets', [])]

    def load_tasks(self, status, project=None, fields=None):
        self.refresh()
        if project is None:
            for project in self.projects:
                for each in self.load_tasks(status, project, fields):
                    yield each
        else:
            for record in elasticsearch.helpers.scan(self.es, index=self.index, doc_type=self.__type__,
                                                     query={'query': {'bool': {
                                                         'must': {'term': {'project': project}},
                                                         'should': [{'term': {'status': status}}],
                                                         'minimum_should_match': 1,
                                                     }}}, _source_include=fields or []):
                yield self._parse(record['_source'])

    def get_task(self, project, taskid, fields=None):
        if self._changed:
            self.refresh()
        ret = self.es.get(index=self.index, doc_type=self.__type__, id="%s:%s" % (project, taskid),
                          _source_include=fields or [], ignore=404)
        return self._parse(ret.get('_source', None))

    def status_count(self, project):
        self.refresh()
        ret = self.es.search(index=self.index, doc_type=self.__type__,
                             body={"query": {'term': {'project': project}},
                                   "aggs": {"status": {
                                       "terms": {"field": "status"}
                                   }}}, _source=False)
        result = {}
        for each in ret['aggregations']['status'].get('buckets', []):
            result[each['key']] = each['doc_count']
        return result

    def insert(self, project, taskid, obj={}):
        self._changed = True
        obj = dict(obj)
        obj['taskid'] = taskid
        obj['project'] = project
        obj['updatetime'] = time.time()
        return self.es.index(index=self.index, doc_type=self.__type__,
                             body=self._stringify(obj), id='%s:%s' % (project, taskid))

    def update(self, project, taskid, obj={}, **kwargs):
        self._changed = True
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        return self.es.update(index=self.index, doc_type=self.__type__, id='%s:%s' % (project, taskid),
                              body={"doc": self._stringify(obj)}, ignore=404)

    def drop(self, project):
        self.refresh()
        for record in elasticsearch.helpers.scan(self.es, index=self.index, doc_type=self.__type__,
                                                 query={'query': {'term': {'project': project}}},
                                                 _source=False):
            self.es.delete(index=self.index, doc_type=self.__type__, id=record['_id'])
        self.refresh()

    def refresh(self):
        """
        Explicitly refresh one or more index, making all operations
        performed since the last refresh available for search.
        """
        self._changed = False
        self.es.indices.refresh(index=self.index)
