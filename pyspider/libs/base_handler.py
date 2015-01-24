#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 23:12:48

import sys
import inspect
import functools
import fractions

import six
from six import add_metaclass, iteritems

from pyspider.libs.log import LogFormatter
from pyspider.libs.url import quote_chinese, _build_url, _encode_params, _encode_multipart_formdata
from pyspider.libs.utils import md5string, hide_me, pretty_unicode
from pyspider.libs.ListIO import ListO
from pyspider.libs.response import rebuild_response
from pyspider.libs.pprint import pprint


class ProcessorResult(object):
    """The result and logs producted by a callback"""

    def __init__(self, result, follows, messages, logs, exception, extinfo):
        self.result = result
        self.follows = follows
        self.messages = messages
        self.logs = logs
        self.exception = exception
        self.extinfo = extinfo

    def rethrow(self):
        """rethrow the exception"""

        if self.exception:
            raise self.exception

    def logstr(self):
        """handler the log records to formatted string"""

        result = []
        formater = LogFormatter(color=False)
        for record in self.logs:
            if isinstance(record, six.string_types):
                result.append(pretty_unicode(record))
            else:
                if record.exc_info:
                    a, b, tb = record.exc_info
                    tb = hide_me(tb, globals())
                    record.exc_info = a, b, tb
                result.append(pretty_unicode(formater.format(record)))
                result.append(u'\n')
        return u''.join(result)


def catch_status_code_error(func):
    """
    Non-200 response will been regarded as fetch failed and will not pass to callback.
    Use this decorator to override this feature.
    """
    func._catch_status_code_error = True
    return func


def not_send_status(func):
    """
    Do not send process status package back to scheduler.

    It's used by callbacks like on_message, on_result etc...
    """
    @functools.wraps(func)
    def wrapper(self, response, task):
        self._extinfo['not_send_status'] = True
        function = func.__get__(self, self.__class__)
        return self._run_func(function, response, task)
    return wrapper


def config(_config=None, **kwargs):
    """
    A decorator for setting the default kwargs of `BaseHandler.crawl`.
    Any self.crawl with this callback will use this config.
    """
    if _config is None:
        _config = {}
    _config.update(kwargs)

    def wrapper(func):
        func._config = _config
        return func
    return wrapper


class NOTSET(object):
    pass


def every(minutes=NOTSET, seconds=NOTSET):
    """
    method will been called every minutes or seconds
    """
    def wrapper(func):
        @functools.wraps(func)
        def on_cronjob(self, response, task):
            if (
                    response.save
                    and 'tick' in response.save
                    and response.save['tick'] % (minutes * 60 + seconds) != 0
            ):
                return None
            function = func.__get__(self, self.__class__)
            return self._run_func(function, response, task)
        on_cronjob.is_cronjob = True
        on_cronjob.tick = minutes * 60 + seconds
        return on_cronjob

    if inspect.isfunction(minutes):
        func = minutes
        minutes = 1
        seconds = 0
        return wrapper(func)

    if minutes is NOTSET:
        if seconds is NOTSET:
            minutes = 1
            seconds = 0
        else:
            minutes = 0
    if seconds is NOTSET:
        seconds = 0

    return wrapper


class BaseHandlerMeta(type):

    def __new__(cls, name, bases, attrs):
        cron_jobs = []
        min_tick = 0

        for each in attrs.values():
            if inspect.isfunction(each) and getattr(each, 'is_cronjob', False):
                cron_jobs.append(each)
                min_tick = fractions.gcd(min_tick, each.tick)
        newcls = type.__new__(cls, name, bases, attrs)
        newcls._cron_jobs = cron_jobs
        newcls._min_tick = min_tick
        return newcls


@add_metaclass(BaseHandlerMeta)
class BaseHandler(object):
    """
    BaseHandler for all scripts.

    `BaseHandler.run` is the main method to handler the task.
    """
    crawl_config = {}
    project_name = None
    _cron_jobs = []
    _min_tick = 0
    __env__ = {'not_inited': True}

    def _reset(self):
        """
        reset before each task
        """
        self._extinfo = {}
        self._messages = []
        self._follows = []
        self._follows_keys = set()

    def _run_func(self, function, *arguments):
        """
        Running callback function with requested number of arguments
        """
        args, varargs, keywords, defaults = inspect.getargspec(function)
        return function(*arguments[:len(args) - 1])

    def _run_task(self, task, response):
        """
        Finding callback specified by `task['callback']`
        raising status error for it if needed.
        """
        self._reset()
        if isinstance(response, dict):
            response = rebuild_response(response)
        process = task.get('process', {})
        callback = process.get('callback', '__call__')
        if not hasattr(self, callback):
            raise NotImplementedError("self.%s() not implemented!" % callback)

        function = getattr(self, callback)
        # do not run_func when 304
        if response.status_code == 304 and not getattr(function, '_catch_status_code_error', False):
            return None
        if not getattr(function, '_catch_status_code_error', False):
            response.raise_for_status()
        return self._run_func(function, response, task)

    def run_task(self, module, task, response):
        """
        Processing the task, catching exceptions and logs, return a `ProcessorResult` object
        """
        logger = module.logger
        result = None
        exception = None
        stdout = sys.stdout
        self.task = task
        self.response = response

        try:
            if self.__env__.get('enable_stdout_capture', True):
                sys.stdout = ListO(module.log_buffer)
            result = self._run_task(task, response)
            if inspect.isgenerator(result):
                for r in result:
                    self._run_func(self.on_result, r, response, task)
            else:
                self._run_func(self.on_result, result, response, task)
        except Exception as e:
            logger.exception(e)
            exception = e
        finally:
            self.task = None
            self.response = None
            sys.stdout = stdout
            follows = self._follows
            messages = self._messages
            logs = list(module.log_buffer)
            extinfo = self._extinfo

        module.log_buffer[:] = []
        return ProcessorResult(result, follows, messages, logs, exception, extinfo)

    def _crawl(self, url, **kwargs):
        """
        real crawl API

        checking kwargs, and repack them to each sub-dict
        """
        task = {}

        if kwargs.get('callback'):
            callback = kwargs['callback']
            if isinstance(callback, six.string_types) and hasattr(self, callback):
                func = getattr(self, callback)
            elif six.callable(callback) and six.get_method_self(callback) is self:
                func = callback
                kwargs['callback'] = func.__name__
            else:
                raise NotImplementedError("self.%s() not implemented!" % callback)
            if hasattr(func, '_config'):
                for k, v in iteritems(func._config):
                    kwargs.setdefault(k, v)

        for k, v in iteritems(self.crawl_config):
            kwargs.setdefault(k, v)

        url = quote_chinese(_build_url(url.strip(), kwargs.get('params')))
        if kwargs.get('files'):
            assert isinstance(
                kwargs.get('data', {}), dict), "data must be a dict when using with files!"
            content_type, data = _encode_multipart_formdata(kwargs.get('data', {}),
                                                            kwargs.get('files', {}))
            kwargs.setdefault('headers', {})
            kwargs['headers']['Content-Type'] = content_type
            kwargs['data'] = data
        if kwargs.get('data'):
            kwargs['data'] = _encode_params(kwargs['data'])
        if kwargs.get('data'):
            kwargs.setdefault('method', 'POST')

        schedule = {}
        for key in ('priority', 'retries', 'exetime', 'age', 'itag', 'force_update'):
            if key in kwargs and kwargs[key] is not None:
                schedule[key] = kwargs[key]
        task['schedule'] = schedule

        fetch = {}
        for key in (
                'method',
                'headers',
                'data',
                'timeout',
                'allow_redirects',
                'cookies',
                'proxy',
                'etag',
                'last_modifed',
                'save',
                'js_run_at',
                'js_script',
                'load_images',
                'fetch_type'
        ):
            if key in kwargs and kwargs[key] is not None:
                fetch[key] = kwargs[key]
        task['fetch'] = fetch

        process = {}
        for key in ('callback', ):
            if key in kwargs and kwargs[key] is not None:
                process[key] = kwargs[key]
        task['process'] = process

        task['project'] = self.project_name
        task['url'] = url
        task['taskid'] = kwargs.get('taskid') or self.get_taskid(task)

        cache_key = "%(project)s:%(taskid)s" % task
        if cache_key not in self._follows_keys:
            self._follows_keys.add(cache_key)
            self._follows.append(task)
        return task

    def get_taskid(self, task):
        '''Generate taskid by information of task md5(url) by default, override me'''
        return md5string(task['url'])

    # apis
    def crawl(self, url, **kwargs):
        '''
        avalable params:
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

          fetch_type
          js_run_at
          js_script
          load_images

          priority
          retries
          exetime
          age
          itag

          save
          taskid

          full documents: http://pyspider.readthedocs.org/en/latest/apis/self.crawl/
        '''

        if isinstance(url, six.string_types):
            return self._crawl(url, **kwargs)
        elif hasattr(url, "__iter__"):
            result = []
            for each in url:
                result.append(self._crawl(each, **kwargs))
            return result

    def is_debugger(self):
        """Return true if running in debugger"""
        return self.__env__.get('debugger')

    def send_message(self, project, msg, url='data:,on_message'):
        """Send messages to other project."""
        self._messages.append((project, msg, url))

    def on_message(self, project, msg):
        """Receive message from other project, override me."""
        pass

    def on_result(self, result):
        """Receiving returns from other callback, override me."""
        if not result:
            return
        assert self.task, "on_result can't outside a callback."
        if self.is_debugger():
            pprint(result)
        if self.__env__.get('result_queue'):
            self.__env__['result_queue'].put((self.task, result))

    @not_send_status
    def _on_message(self, response):
        project, msg = response.save
        return self.on_message(project, msg)

    @not_send_status
    def _on_cronjob(self, response, task):
        for cronjob in self._cron_jobs:
            function = cronjob.__get__(self, self.__class__)
            self._run_func(function, response, task)

    @not_send_status
    def _on_get_info(self, response, task):
        """Sending runtime infomation about this script."""
        result = {}
        assert response.save
        for each in response.save:
            if each == 'min_tick':
                result[each] = self._min_tick
        self.crawl('data:,on_get_info', save=result)
