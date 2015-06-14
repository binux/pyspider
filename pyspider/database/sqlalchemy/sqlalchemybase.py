#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-04 18:48:47

import time


def result2dict(columns, task):
    r = {}
    for key in task.keys():
        r[key] = task[key]
    return r


class SplitTableMixin(object):
    UPDATE_PROJECTS_TIME = 10 * 60

    def _tablename(self, project):
        if self.__tablename__:
            return '%s_%s' % (self.__tablename__, project)
        else:
            return project

    @property
    def projects(self):
        if time.time() - getattr(self, '_last_update_projects', 0) \
                > self.UPDATE_PROJECTS_TIME:
            self._list_project()
        return self._projects

    @projects.setter
    def projects(self, value):
        self._projects = value

    def _list_project(self):
        self._last_update_projects = time.time()
        self.projects = set()
        if self.__tablename__:
            prefix = '%s_' % self.__tablename__
        else:
            prefix = ''

        for project in self.engine.table_names():
            if project.startswith(prefix):
                project = project[len(prefix):]
                self.projects.add(project)

    def drop(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        self.table.name = self._tablename(project)
        self.table.drop(self.engine)
        self._list_project()
