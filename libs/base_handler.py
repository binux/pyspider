#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 23:12:48

import time
import inspect
from libs.response import rebuild_response
from collections import namedtuple


ProcessorResult = namedtuple('ProcessorResult', 'result, follows, messages, logs, exception, extinfo')


class BaseHandlerMeta(type):
    def __new__(cls, name, bases, attrs):
        return type.__new__(cls, name, bases, attrs)


class BaseHandler(object):
    __metaclass__ = Meta

    def _init(self, project):
        self._name = project['name']
        self._project = project

        self._reset()

    def _reset(self):
        self._extinfo = {}
        self._messages = []
        self._follows = []

    def _run(self, task, response):
        response = rebuild_response(response)
        process = task.get('process', {})
        callback = process.get('callback', '__call__')
        if not hasattr(self, callback):
            raise NotImplementedError("self.%s() not implemented!" % callback)

        function = getattr(self, callback)
        args, varargs, keywords, defaults = inspect.getargspec(function)
        if len(args) == 1: # foo(self)
            return function()
        elif len(args) == 2: # foo(self, response)
            return function(response)
        elif len(args) == 3: # foo(self, response, save)
            return function(response, process.get('save'))
        elif len(args) == 4: # foo(self, response, save, task)
            return function(response, process.get('save'), task)
        else:
            raise TypeError("self.%s() need at least 1 argument and lesser 4 arguments: %s(self, [response], [save], [task])" % (function.__name__, function.__name__))
            
    def run(self, module, task, response):
        logger = module.get('logger')
        result = None
        exception = None

        try:
            result = self._run(task, response)
        except Exception, e:
            logger.exception(e)
            exception = e
        finally:
            follows = self._follows
            messages = self._messages
            logs = list(module.logs)
            extinfo = self._extinfo

            self._reset()
        return ProcessorResult(result, follows, messages, logs, exception, extinfo)

    def _crawl(self, url, **kwargs):
        task = {}

        if kwargs.get('callback'):
            callback = kwargs['callback']
            if isinstance(callback, basestring) and hasattr(self, callback):
                func = getattr(self, callback)
            elif hasattr(callback, 'im_self') and callback.im_self is self:
                func = callback
                kwargs['callback'] = func.__name__
            else:
                raise NotImplementedError("self.%s() not implemented!" % callback)
            if hasattr(func, '_config'):
                for k, v in func._config.iteritems():
                    kwargs.setdefault(k, v)

        if hasattr(self, 'crawl_config'):
            for k, v in self.crawl_config.iteritems():
                kwargs.setdefault(k, v)

        url = quote_chinese(_build_url(url.strip(), kwargs.get('params')))
        if kwargs.get('files'):
            assert isinstance(kwargs.get('data', {}), dict), "data must be a dict when using with files!"
            content_type, data = _encode_multipart_formdata(kwargs.get('data', {}),
                                                            kwargs.get('files', {}))
            kwargs.setdefault('headers', {})
            kwargs['headers']['Content-Type'] = content_type
            kwargs['data'] = data
        if kwargs.get('data'):
            kwargs['data'] = _encode_params(kwargs['data'])

        schedule = {}
        for key in ('priority', 'retries', 'exetime', 'age', 'itag'):
            if key in kwargs and kwargs[key] is not None:
                schedule[key] = kwargs[key]
        if schedule:
            task['schedule'] = schedule

        fetch = {}
        for key in ('method', 'headers', 'data', 'timeout', 'allow_redirects', 'cookies', 'proxy', 'etag', 'last_modifed'):
            if key in kwargs and kwargs[key] is not None:
                fetch[key] = kwargs[key]
        if fetch:
            task['fetch'] = fetch

        process = {}
        for key in ('callback', 'save'):
            if key in kwargs and kwargs[key] is not None:
                process[key] = kwargs[key]
        if process:
            task['process'] = process

        task['project'] = self._name
        task['url'] = url
        task['rowid'] = task.get('rowid') or md5string(url)

        self._follows.append(task)
        return task

    # apis
    def crawl(self, url, **kwargs):
        '''
        params:
          url
          callback

          method
          params
          data
          files
          headers
          timeout
          allow_redirects
          cookies
          proxy
          etag
          last_modifed

          priority
          retries
          exetime
          age
          itag

          save
          rowid
        '''


        if isinstance(url, basestring):
            return self._crawl(url, **kwargs)
        elif hasattr(url, "__iter__"):
            result = []
            for each in url:
                result.append(self._crawl(each, **kwargs))
            return result

    def send_message(self, project, msg):
        self._messages.append((project, msg))

    def on_message(self, response, msg):
        pass
