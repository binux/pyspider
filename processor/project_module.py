#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 22:24:20

import sys
import logging
import inspect
import linecache
from libs import base_handler
from libs.log import SaveLogHandler

class ObjectDict(dict):
    def __getattr__(self, name):
        return self.__getitem__(name)

class ProjectModule(object):
    def __init__(self, name, script, env={}):
        self.name = name
        self.name_fixed = name.replace('.', '_')
        self.script = script
        self.env = env
        self.error = None
        self.exc_info = None

        self._log_buffer = []
        self._logger = logging.Logger()
        self._logger.addHandler(SaveLogHandler(self._log_buffer))

        self._build_module()

    def _build_module(self):
        self._module = object()
        self._module.__dict__ = {
                'logging': self._logger,
                'logger': self._logger,
                '__env__': self.env,
                '__name__': self.name_fixed,
                '__loader__': ObjectDict(get_source=lambda name: self.script.encode('utf8')),
                }
        try:
            exec compile(self.script, self.name_fixed+'.py', 'exec') in self._module.__dict__
            linecache.clearcache()
        except Exception, e:
            self.exc_info = sys.exc_info()
            self.error = e
            logging.exception(e)

    def rethrow(self):
        if self.exc_info:
            raise self.exc_info[0], self.exc_info[1], self.exc_info[2]

    def get(self, key='__class__', default=None):
        if key is '__class__' and '__class__' not in self._module.__dict__:
            for each in self._module.__dict__.values():
                if inspect.isclass(each) and each is not base_handler.BaseHandler \
                        and issubclass(each, base_handler.BaseHandler):
                            self._module.__dict__['__class__'] = each
                            break
        return self._module.__dict__.get(key, default)

    @property
    def logs(self):
        return self._log_buffer
