#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2016-01-17 18:32:33

import time

import elasticsearch.helpers
from elasticsearch import Elasticsearch
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB


class ProjectDB(BaseProjectDB):
    __type__ = 'project'

    def __init__(self, hosts, index='pyspider'):
        self.index = index
        self.es = Elasticsearch(hosts=hosts)

        self.es.indices.create(index=self.index, ignore=400)
        if not self.es.indices.get_mapping(index=self.index, doc_type=self.__type__):
            self.es.indices.put_mapping(index=self.index, doc_type=self.__type__, body={
                "_all": {"enabled": False},
                "properties": {
                    "updatetime": {"type": "double"}
                }
            })

    def insert(self, name, obj={}):
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()

        obj.setdefault('group', '')
        obj.setdefault('status', 'TODO')
        obj.setdefault('script', '')
        obj.setdefault('comments', '')
        obj.setdefault('rate', 0)
        obj.setdefault('burst', 0)

        return self.es.index(index=self.index, doc_type=self.__type__, body=obj, id=name,
                             refresh=True)

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        return self.es.update(index=self.index, doc_type=self.__type__,
                              body={'doc': obj}, id=name, refresh=True, ignore=404)

    def get_all(self, fields=None):
        for record in elasticsearch.helpers.scan(self.es, index=self.index, doc_type=self.__type__,
                                                 query={'query': {"match_all": {}}},
                                                 _source_include=fields or []):
            yield record['_source']

    def get(self, name, fields=None):
        ret = self.es.get(index=self.index, doc_type=self.__type__, id=name,
                          _source_include=fields or [], ignore=404)
        return ret.get('_source', None)

    def check_update(self, timestamp, fields=None):
        for record in elasticsearch.helpers.scan(self.es, index=self.index, doc_type=self.__type__,
                                                 query={'query': {"range": {
                                                     "updatetime": {"gte": timestamp}
                                                 }}}, _source_include=fields or []):
            yield record['_source']

    def drop(self, name):
        return self.es.delete(index=self.index, doc_type=self.__type__, id=name, refresh=True)
