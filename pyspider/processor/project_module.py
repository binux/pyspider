#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 22:24:20

import sys
import imp
import logging
import inspect
import linecache
from pyspider.libs import base_handler
from pyspider.libs.log import SaveLogHandler


class ProjectFinder(object):

    def find_module(self, fullname, path=None):
        if fullname == 'projects':
            return ProjectsLoader()
        parts = fullname.split('.')
        if len(parts) == 2 and parts[0] == 'projects':
            return self.get_loader(parts[1])


class ProjectsLoader(object):

    def load_module(self, fullname):
        mod = sys.modules.setdefault('projects', imp.new_module(fullname))
        mod.__file__ = '<projects>'
        mod.__loader__ = self
        mod.__path__ = []
        mod.__package__ = 'projects'
        return mod


class ProjectLoader(object):

    def __init__(self, project, mod=None):
        self.project = project
        self.name = project['name']
        self.mod = mod

    def load_module(self, fullname):
        if self.mod is None:
            mod = self.mod = imp.new_module(self.name)
        else:
            mod = self.mod

        log_buffer = []
        mod.logging = mod.logger = logging.Logger(self.name)
        mod.logger.addHandler(SaveLogHandler(log_buffer))
        mod.log_buffer = log_buffer
        mod.__file__ = '<%s>' % self.name
        mod.__loader__ = self
        mod.__project__ = self.project
        mod.__package__ = ''

        code = self.get_code(fullname)
        exec code in mod.__dict__
        linecache.clearcache()

        if '__handler_cls__' not in mod.__dict__:
            BaseHandler = mod.__dict__.get('BaseHandler', base_handler.BaseHandler)
            for each in mod.__dict__.values():
                if inspect.isclass(each) and each is not BaseHandler \
                        and issubclass(each, BaseHandler):
                    mod.__dict__['__handler_cls__'] = each

        return mod

    def is_package(self, fullname):
        return False

    def get_code(self, fullname):
        return compile(self.get_source(fullname), '<%s>' % self.name, 'exec')

    def get_source(self, fullname):
        script = self.project['script']
        if isinstance(script, unicode):
            return script.encode('utf8')
        return script
