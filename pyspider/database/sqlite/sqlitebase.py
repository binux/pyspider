#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-22 20:30:44

import os
import time
import sqlite3
import threading


class SQLiteMixin(object):

    @property
    def dbcur(self):
        pid = (os.getpid(), threading.current_thread().ident)
        if not (self.conn and pid == self.last_pid):
            self.last_pid = pid
            self.conn = sqlite3.connect(self.path, isolation_level=None)
        return self.conn.cursor()


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
        for project, in self._select('sqlite_master', what='name',
                                     where='type = "table"'):
            if project.startswith(prefix):
                project = project[len(prefix):]
                self.projects.add(project)

    def drop(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        tablename = self._tablename(project)
        self._execute("DROP TABLE %s" % self.escape(tablename))
        self._list_project()
