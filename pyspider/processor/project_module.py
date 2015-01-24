#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 22:24:20

import os
import six
import sys
import imp
import time
import logging
import inspect
import linecache
from pyspider.libs import base_handler
from pyspider.libs.log import SaveLogHandler, LogFormatter
logger = logging.getLogger("processor")


class ProjectManager(object):
    """
    load projects from projectdb, update project
    """

    CHECK_PROJECTS_INTERVAL = 5 * 60
    RELOAD_PROJECT_INTERVAL = 60 * 60

    @staticmethod
    def build_module(project, env={}):
        '''Build project script as module'''
        assert 'name' in project, 'need name of project'
        assert 'script' in project, 'need script of project'

        # fix for old non-package version scripts
        pyspider_path = os.path.join(os.path.dirname(__file__), "..")
        if pyspider_path not in sys.path:
            sys.path.insert(1, pyspider_path)

        env = dict(env)
        env.update({
            'debug': project.get('status', 'DEBUG') == 'DEBUG',
        })

        loader = ProjectLoader(project)
        module = loader.load_module(project['name'])

        # logger inject
        module.log_buffer = []
        module.logging = module.logger = logging.Logger(project['name'])
        if env.get('enable_stdout_capture', True):
            handler = SaveLogHandler(module.log_buffer)
            handler.setFormatter(LogFormatter(color=False))
        else:
            handler = logging.StreamHandler()
            handler.setFormatter(LogFormatter(color=True))
        module.logger.addHandler(handler)

        if '__handler_cls__' not in module.__dict__:
            BaseHandler = module.__dict__.get('BaseHandler', base_handler.BaseHandler)
            for each in list(six.itervalues(module.__dict__)):
                if inspect.isclass(each) and each is not BaseHandler \
                        and issubclass(each, BaseHandler):
                    module.__dict__['__handler_cls__'] = each
        _class = module.__dict__.get('__handler_cls__')
        assert _class is not None, "need BaseHandler in project module"

        instance = _class()
        instance.__env__ = env
        instance.project_name = project['name']
        instance.project = project

        return {
            'loader': loader,
            'module': module,
            'class': _class,
            'instance': instance,
            'info': project,
            'load_time': time.time(),
        }

    def __init__(self, projectdb, env):
        self.projectdb = projectdb
        self.env = env

        self.projects = {}
        self.last_check_projects = time.time()

    def _need_update(self, project_name, updatetime=None):
        '''Check if project_name need update'''
        if project_name not in self.projects:
            return True
        if updatetime and updatetime > self.projects[project_name]['info'].get('updatetime', 0):
            return True
        if time.time() - self.projects[project_name]['load_time'] > self.RELOAD_PROJECT_INTERVAL:
            return True
        return False

    def _check_projects(self):
        '''Check projects by last update time'''
        for project in self.projectdb.check_update(self.last_check_projects,
                                                   ['name', 'updatetime']):
            if project['name'] not in self.projects:
                continue
            if project['updatetime'] > self.projects[project['name']]['info'].get('updatetime', 0):
                self._update_project(project['name'])
        self.last_check_projects = time.time()

    def _update_project(self, project_name):
        '''Update one project from database'''
        project = self.projectdb.get(project_name)
        if not project:
            return None
        return self._load_project(project)

    def _load_project(self, project):
        '''Load project into self.projects from project info dict'''
        try:
            ret = self.build_module(project, self.env)
            self.projects[project['name']] = ret
        except Exception:
            logger.exception("load project %s error", project.get('name', None))
            return False
        logger.debug('project: %s updated.', project.get('name', None))
        return True

    def get(self, project_name, updatetime=None):
        '''get project data object, return None if not exists'''
        if time.time() - self.last_check_projects < self.CHECK_PROJECTS_INTERVAL:
            self._check_projects()
        if self._need_update(project_name, updatetime):
            self._update_project(project_name)
        return self.projects.get(project_name, None)


class ProjectFinder(object):
    '''ProjectFinder class for sys.meta_path'''

    def find_module(self, fullname, path=None):
        if fullname == 'projects':
            return ProjectsLoader()
        parts = fullname.split('.')
        if len(parts) == 2 and parts[0] == 'projects':
            return self.get_loader(parts[1])


class ProjectsLoader(object):
    '''ProjectsLoader class for sys.meta_path package'''

    def load_module(self, fullname):
        mod = sys.modules.setdefault('projects', imp.new_module(fullname))
        mod.__file__ = '<projects>'
        mod.__loader__ = self
        mod.__path__ = []
        mod.__package__ = 'projects'
        return mod


class ProjectLoader(object):
    '''ProjectLoader class for sys.meta_path'''

    def __init__(self, project, mod=None):
        self.project = project
        self.name = project['name']
        self.mod = mod

    def load_module(self, fullname):
        if self.mod is None:
            mod = self.mod = imp.new_module(self.name)
        else:
            mod = self.mod

        mod.__file__ = '<%s>' % self.name
        mod.__loader__ = self
        mod.__project__ = self.project
        mod.__package__ = ''
        code = self.get_code(fullname)
        six.exec_(code, mod.__dict__)
        linecache.clearcache()
        return mod

    def is_package(self, fullname):
        return False

    def get_code(self, fullname):
        return compile(self.get_source(fullname), '<%s>' % self.name, 'exec')

    def get_source(self, fullname):
        script = self.project['script']
        if isinstance(script, six.text_type):
            return script.encode('utf8')
        return script
