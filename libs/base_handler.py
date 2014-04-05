#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 23:12:48

import os
import sys
import time
import inspect
import functools
import traceback
from libs.log import LogFormatter
from libs.url import quote_chinese, _build_url
from libs.utils import md5string, hide_me
from libs.ListIO import ListO
from libs.response import rebuild_response
from collections import namedtuple

class ProcessorResult(object):
    def __init__(self, result, follows, messages, logs, exception, extinfo):
        self.result = result
        self.follows = follows
        self.messages = messages
        self.logs = logs
        self.exception = exception
        self.extinfo = extinfo

    def rethrow(self):
        if self.exception:
            raise self.exception

    def logstr(self):
        result = []
        formater = LogFormatter(color=False)
        for record in self.logs:
            if isinstance(record, basestring):
                result.append(record)
                continue
            else:
                if record.exc_info:
                    a, b, tb = record.exc_info
                    tb = hide_me(tb, globals())
                    record.exc_info = a, b, tb
                result.append(formater.format(record))
                result.append('\n')
        return ''.join(result)

def catch_status_code_error(func):
    func._catch_status_code_error = True
    return func

def not_send_status(func):
    @functools.wraps(func)
    def wrapper(self, response, task):
        self._extinfo['not_send_status'] = True
        function = func.__get__(self, self.__class__)
        return self._run_func(function, response, task)
    return wrapper

def config(_config):
    def wrapper(func):
        func._config = _config
        return func
    return wrapper

def every(minutes=1):
    def wrapper(func):
        @functools.wraps(func)
        def on_cronjob(self, response, task):
            if response.save and 'tick' in response.save and response.save['tick'] % minutes == 0:
                function = func.__get__(self, self.__class__)
                return self._run_func(function, response, task)
            return None
        return on_cronjob
    return wrapper


class BaseHandlerMeta(type):
    def __new__(cls, name, bases, attrs):
        if '_on_message' in attrs:
            attrs['_on_message'] = not_send_status(attrs['_on_message'])
        if 'on_cronjob' in attrs:
            attrs['on_cronjob'] = not_send_status(attrs['on_cronjob'])
        return type.__new__(cls, name, bases, attrs)


class BaseHandler(object):
    __metaclass__ = BaseHandlerMeta

    def _reset(self):
        self._extinfo = {}
        self._messages = []
        self._follows = []

    def _run_func(self, function, *arguments):
        args, varargs, keywords, defaults = inspect.getargspec(function)
        return function(*arguments[:len(args)-1])

    def _run(self, task, response):
        self._reset()
        if isinstance(response, dict):
            response = rebuild_response(response)
        process = task.get('process', {})
        callback = process.get('callback', '__call__')
        if not hasattr(self, callback):
            raise NotImplementedError("self.%s() not implemented!" % callback)

        function = getattr(self, callback)
        if not getattr(function, '_catch_status_code_error', False):
            response.raise_for_status()
        return self._run_func(function, response, task)
            
    def run(self, module, task, response):
        logger = module.logger
        result = None
        exception = None
        stdout = sys.stdout

        try:
            sys.stdout = ListO(module.log_buffer)
            result = self._run(task, response)
            self._run_func(self.on_result, result, response, task)
        except Exception, e:
            logger.exception(e)
            exception = e
        finally:
            sys.stdout = stdout
            follows = self._follows
            messages = self._messages
            logs = module.log_buffer
            extinfo = self._extinfo

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
        for key in ('priority', 'retries', 'exetime', 'age', 'itag', 'force_update'):
            if key in kwargs and kwargs[key] is not None:
                schedule[key] = kwargs[key]
        if schedule:
            task['schedule'] = schedule

        fetch = {}
        for key in ('method', 'headers', 'data', 'timeout', 'allow_redirects', 'cookies', 'proxy', 'etag', 'last_modifed', 'save'):
            if key in kwargs and kwargs[key] is not None:
                fetch[key] = kwargs[key]
        if fetch:
            task['fetch'] = fetch

        process = {}
        for key in ('callback', ):
            if key in kwargs and kwargs[key] is not None:
                process[key] = kwargs[key]
        if process:
            task['process'] = process

        task['project'] = __name__
        task['url'] = url
        task['taskid'] = task.get('taskid') or md5string(url)

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
          taskid
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

    @not_send_status
    def _on_message(self, response):
        project, msg = response.save
        return self.on_message(project, msg)

    def on_message(self, project, msg):
        pass

    def on_cronjob(self):
        pass

    def on_result(self, result):
        pass
