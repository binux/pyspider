#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-22 20:42:01

import time


class SplitTableMixin(object):
    UPDATE_PROJECTS_TIME = 10 * 60

    def _collection_name(self, project):
        if self.collection_prefix:
            return "%s.%s" % (self.collection_prefix, project)
        else:
            return project

    @property
    def projects(self):
        if time.time() - getattr(self, '_last_update_projects', 0) > self.UPDATE_PROJECTS_TIME:
            self._list_project()
        return self._projects

    @projects.setter
    def projects(self, value):
        self._projects = value

    def _list_project(self):
        self._last_update_projects = time.time()
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

    def drop(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        self.database[collection_name].drop()
        self._list_project()
