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

from pyspider.libs.url import (
    quote_chinese, _build_url, _encode_params,
    _encode_multipart_formdata, curl_to_arguments)
from pyspider.libs.utils import md5string, timeout
from pyspider.libs.ListIO import ListO
from pyspider.libs.response import rebuild_response
from pyspider.libs.pprint import pprint
from pyspider.processor import ProcessorResult


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
        # mark the function with variable 'is_cronjob=True', the function would be
        # collected into the list Handler._cron_jobs by meta class
        func.is_cronjob = True

        # collect interval and unify to seconds, it's used in meta class. See the
        # comments in meta class.
        func.tick = minutes * 60 + seconds
        return func

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
        # A list of all functions which is marked as 'is_cronjob=True'
        cron_jobs = []

        # The min_tick is the greatest common divisor(GCD) of the interval of cronjobs
        # this value would be queried by scheduler when the project initial loaded.
        # Scheudler may only send _on_cronjob task every min_tick seconds. It can reduce
        # the number of tasks sent from scheduler.
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
    retry_delay = {}

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
        task = arguments[-1]
        process_time_limit = task['process'].get('process_time_limit',
                                                 self.__env__.get('process_time_limit', 0))
        if process_time_limit > 0:
            with timeout(process_time_limit, 'process timeout'):
                ret = function(*arguments[:len(args) - 1])
        else:
            ret = function(*arguments[:len(args) - 1])
        return ret

    def _run_task(self, task, response):
        """
        Finding callback specified by `task['callback']`
        raising status error for it if needed.
        """
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
        self.logger = logger = module.logger
        result = None
        exception = None
        stdout = sys.stdout
        self.task = task
        if isinstance(response, dict):
            response = rebuild_response(response)
        self.response = response
        self.save = (task.get('track') or {}).get('save', {})

        try:
            if self.__env__.get('enable_stdout_capture', True):
                sys.stdout = ListO(module.log_buffer)
            self._reset()
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
            follows = self._follows
            messages = self._messages
            logs = list(module.log_buffer)
            extinfo = self._extinfo
            save = self.save

            sys.stdout = stdout
            self.task = None
            self.response = None
            self.save = None

        module.log_buffer[:] = []
        return ProcessorResult(result, follows, messages, logs, exception, extinfo, save)

    schedule_fields = ('priority', 'retries', 'exetime', 'age', 'itag', 'force_update', 'auto_recrawl', 'cancel')
    fetch_fields = ('method', 'headers', 'user_agent', 'data', 'connect_timeout', 'timeout', 'allow_redirects', 'cookies',
                    'proxy', 'etag', 'last_modifed', 'last_modified', 'save', 'js_run_at', 'js_script',
                    'js_viewport_width', 'js_viewport_height', 'load_images', 'fetch_type', 'use_gzip', 'validate_cert',
                    'max_redirects', 'robots_txt')
    process_fields = ('callback', 'process_time_limit')

    @staticmethod
    def task_join_crawl_config(task, crawl_config):
        task_fetch = task.get('fetch', {})
        for k in BaseHandler.fetch_fields:
            if k in crawl_config:
                v = crawl_config[k]
                if isinstance(v, dict) and isinstance(task_fetch.get(k), dict):
                    v = dict(v)
                    v.update(task_fetch[k])
                    task_fetch[k] = v
                else:
                    task_fetch.setdefault(k, v)
        if task_fetch:
            task['fetch'] = task_fetch

        task_process = task.get('process', {})
        for k in BaseHandler.process_fields:
            if k in crawl_config:
                v = crawl_config[k]
                if isinstance(v, dict) and isinstance(task_process.get(k), dict):
                    task_process[k].update(v)
                else:
                    task_process.setdefault(k, v)
        if task_process:
            task['process'] = task_process

        return task

    def _crawl(self, url, **kwargs):
        """
        real crawl API

        checking kwargs, and repack them to each sub-dict
        """
        task = {}

        assert len(url) < 1024, "Maximum (1024) URL length error."

        if kwargs.get('callback'):
            callback = kwargs['callback']
            if isinstance(callback, six.string_types) and hasattr(self, callback):
                func = getattr(self, callback)
            elif six.callable(callback) and six.get_method_self(callback) is self:
                func = callback
                kwargs['callback'] = func.__name__
            elif six.callable(callback) and hasattr(self, callback.__name__):
                func = getattr(self, callback.__name__)
                kwargs['callback'] = func.__name__
            else:
                raise NotImplementedError("self.%s() not implemented!" % callback)
            if hasattr(func, '_config'):
                for k, v in iteritems(func._config):
                    if isinstance(v, dict) and isinstance(kwargs.get(k), dict):
                        kwargs[k].update(v)
                    else:
                        kwargs.setdefault(k, v)

        url = quote_chinese(_build_url(url.strip(), kwargs.pop('params', None)))
        if kwargs.get('files'):
            assert isinstance(
                kwargs.get('data', {}), dict), "data must be a dict when using with files!"
            content_type, data = _encode_multipart_formdata(kwargs.pop('data', {}),
                                                            kwargs.pop('files', {}))
            kwargs.setdefault('headers', {})
            kwargs['headers']['Content-Type'] = content_type
            kwargs['data'] = data
        if kwargs.get('data'):
            kwargs['data'] = _encode_params(kwargs['data'])
        if kwargs.get('data'):
            kwargs.setdefault('method', 'POST')

        if kwargs.get('user_agent'):
            kwargs.setdefault('headers', {})
            kwargs['headers']['User-Agent'] = kwargs.get('user_agent')

        schedule = {}
        for key in self.schedule_fields:
            if key in kwargs:
                schedule[key] = kwargs.pop(key)
            elif key in self.crawl_config:
                schedule[key] = self.crawl_config[key]

        task['schedule'] = schedule

        fetch = {}
        for key in self.fetch_fields:
            if key in kwargs:
                fetch[key] = kwargs.pop(key)
        task['fetch'] = fetch

        process = {}
        for key in self.process_fields:
            if key in kwargs:
                process[key] = kwargs.pop(key)
        task['process'] = process

        task['project'] = self.project_name
        task['url'] = url
        if 'taskid' in kwargs:
            task['taskid'] = kwargs.pop('taskid')
        else:
            task['taskid'] = self.get_taskid(task)

        if kwargs:
            raise TypeError('crawl() got unexpected keyword argument: %s' % kwargs.keys())

        if self.is_debugger():
            task = self.task_join_crawl_config(task, self.crawl_config)

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
        available params:
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
          last_modified
          auto_recrawl

          fetch_type
          js_run_at
          js_script
          js_viewport_width
          js_viewport_height
          load_images

          priority
          retries
          exetime
          age
          itag
          cancel

          save
          taskid

          full documents: http://pyspider.readthedocs.org/en/latest/apis/self.crawl/
        '''

        if isinstance(url, six.string_types) and url.startswith('curl '):
            curl_kwargs = curl_to_arguments(url)
            url = curl_kwargs.pop('urls')
            for k, v in iteritems(curl_kwargs):
                kwargs.setdefault(k, v)

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

    def on_finished(self, response, task):
        """
        Triggered when all tasks in task queue finished.
        http://docs.pyspider.org/en/latest/About-Projects/#on_finished-callback
        """
        pass

    @not_send_status
    def _on_message(self, response):
        project, msg = response.save
        return self.on_message(project, msg)

    @not_send_status
    def _on_cronjob(self, response, task):
        if (not response.save
                or not isinstance(response.save, dict)
                or 'tick' not in response.save):
            return

        # When triggered, a '_on_cronjob' task is sent from scheudler with 'tick' in
        # Response.save. Scheduler may at least send the trigger task every GCD of the
        # inverval of the cronjobs. The method should check the tick for each cronjob
        # function to confirm the execute interval.
        for cronjob in self._cron_jobs:
            if response.save['tick'] % cronjob.tick != 0:
                continue
            function = cronjob.__get__(self, self.__class__)
            self._run_func(function, response, task)

    def _on_get_info(self, response, task):
        """Sending runtime infomation about this script."""
        for each in response.save or []:
            if each == 'min_tick':
                self.save[each] = self._min_tick
            elif each == 'retry_delay':
                if not isinstance(self.retry_delay, dict):
                    self.retry_delay = {'': self.retry_delay}
                self.save[each] = self.retry_delay
            elif each == 'crawl_config':
                self.save[each] = self.crawl_config
