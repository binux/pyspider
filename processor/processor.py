#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 22:59:56

import sys
import time
import logging
import project_module
logger = logging.getLogger("processor")


class Processor(object):
    CHECK_PROJECTS_INTERVAL = 5*60

    def __init__(self, inqueue, status_queue, newtask_queue, projectdb):
        self.inqueue = inqueue
        self.status_queue = status_queue
        self.newtask_queue = newtask_queue
        self.projectdb = projectdb

        self.projects = {}
        self.last_check_projects = 0

    def _init_projects(self):
        for project in self.projectdb.get_all():
            try:
                self._update_project(project)
            except Exception, e:
                logger.exception("exception when init projects for %s" % project.get('name', None))
                continue
        self.last_check_projects = time.time()

    def _check_projects(self):
        if time.time() - self.last_check_projects < self.CHECK_PROJECTS_INTERVAL:
            return
        for project in self.projectdb.check_update(self.last_check_projects):
            try:
                self._update_project(project)
            except Exception, e:
                logger.exception("exception when check update for %s" % project.get('name', None))
                continue
        self.last_check_projects = time.time()

    def _update_project(self, project):
        assert 'name' in project, 'need name of project'
        assert 'script' in project, 'need script of project'

        env = {
            'project': project,
            'debug': project.get('status', 'DEBUG') == 'DEBUG',
            }

        module = project_module.ProjectModule(project['name'], project['script'], env)
        module.rethrow()
        _class = module.get('__class__')
        assert _class is not None, "need BaseHandler in project module"
        instance = _class()._init(project)

        self.projects[project['name']] = {
                'module': module,
                'class': _class,
                'instance': instance,
                'info': project
                }

    def on_task(self, task, response):
        try:
            project = task['project']
            if project not in self.projects:
                raise LookupError("not such project: %s" % project)
            project_data = self.projects[project]
            ret = project_data['instance'].run(project_data['module'], task, response)
        except Exception, e:
            pass
