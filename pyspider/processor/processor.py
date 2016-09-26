#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 22:59:56

import sys
import six
import time
import logging
import traceback
logger = logging.getLogger("processor")

from six.moves import queue as Queue
from pyspider.libs import utils
from pyspider.libs.log import LogFormatter
from pyspider.libs.utils import pretty_unicode, hide_me
from pyspider.libs.response import rebuild_response
from .project_module import ProjectManager, ProjectFinder


class ProcessorResult(object):
    """The result and logs producted by a callback"""

    def __init__(self, result=None, follows=(), messages=(),
                 logs=(), exception=None, extinfo={}, save=None):
        self.result = result
        self.follows = follows
        self.messages = messages
        self.logs = logs
        self.exception = exception
        self.extinfo = extinfo
        self.save = save

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


class Processor(object):
    PROCESS_TIME_LIMIT = 30
    EXCEPTION_LIMIT = 3

    RESULT_LOGS_LIMIT = 1000
    RESULT_RESULT_LIMIT = 10

    def __init__(self, projectdb, inqueue, status_queue, newtask_queue, result_queue,
                 enable_stdout_capture=True,
                 enable_projects_import=True,
                 process_time_limit=PROCESS_TIME_LIMIT):
        self.inqueue = inqueue
        self.status_queue = status_queue
        self.newtask_queue = newtask_queue
        self.result_queue = result_queue
        self.projectdb = projectdb
        self.enable_stdout_capture = enable_stdout_capture

        self._quit = False
        self._exceptions = 10
        self.project_manager = ProjectManager(projectdb, dict(
            result_queue=self.result_queue,
            enable_stdout_capture=self.enable_stdout_capture,
            process_time_limit=process_time_limit,
        ))

        if enable_projects_import:
            self.enable_projects_import()

    def enable_projects_import(self):
        '''
        Enable import other project as module

        `from project import project_name`
        '''
        if six.PY2:
            sys.meta_path.append(ProjectFinder(self.projectdb))

    def __del__(self):
        pass

    def on_task(self, task, response):
        '''Deal one task'''
        start_time = time.time()
        response = rebuild_response(response)

        try:
            assert 'taskid' in task, 'need taskid in task'
            project = task['project']
            updatetime = task.get('project_updatetime', None)
            md5sum = task.get('project_md5sum', None)
            project_data = self.project_manager.get(project, updatetime, md5sum)
            assert project_data, "no such project!"
            if project_data.get('exception'):
                ret = ProcessorResult(logs=(project_data.get('exception_log'), ),
                                      exception=project_data['exception'])
            else:
                ret = project_data['instance'].run_task(
                    project_data['module'], task, response)
        except Exception as e:
            logstr = traceback.format_exc()
            ret = ProcessorResult(logs=(logstr, ), exception=e)
        process_time = time.time() - start_time

        if not ret.extinfo.get('not_send_status', False):
            if ret.exception:
                track_headers = dict(response.headers)
            else:
                track_headers = {}
                for name in ('etag', 'last-modified'):
                    if name not in response.headers:
                        continue
                    track_headers[name] = response.headers[name]

            status_pack = {
                'taskid': task['taskid'],
                'project': task['project'],
                'url': task.get('url'),
                'track': {
                    'fetch': {
                        'ok': response.isok(),
                        'redirect_url': response.url if response.url != response.orig_url else None,
                        'time': response.time,
                        'error': response.error,
                        'status_code': response.status_code,
                        'encoding': getattr(response, '_encoding', None),
                        'headers': track_headers,
                        'content': response.text[:500] if ret.exception else None,
                    },
                    'process': {
                        'ok': not ret.exception,
                        'time': process_time,
                        'follows': len(ret.follows),
                        'result': (
                            None if ret.result is None
                            else utils.text(ret.result)[:self.RESULT_RESULT_LIMIT]
                        ),
                        'logs': ret.logstr()[-self.RESULT_LOGS_LIMIT:],
                        'exception': ret.exception,
                    },
                    'save': ret.save,
                },
            }
            if 'schedule' in task:
                status_pack['schedule'] = task['schedule']

            # FIXME: unicode_obj should used in scheduler before store to database
            # it's used here for performance.
            self.status_queue.put(utils.unicode_obj(status_pack))

        # FIXME: unicode_obj should used in scheduler before store to database
        # it's used here for performance.
        if ret.follows:
            for each in (ret.follows[x:x + 1000] for x in range(0, len(ret.follows), 1000)):
                self.newtask_queue.put([utils.unicode_obj(newtask) for newtask in each])

        for project, msg, url in ret.messages:
            try:
                self.on_task({
                    'taskid': utils.md5string(url),
                    'project': project,
                    'url': url,
                    'process': {
                        'callback': '_on_message',
                    }
                }, {
                    'status_code': 200,
                    'url': url,
                    'save': (task['project'], msg),
                })
            except Exception as e:
                logger.exception('Sending message error.')
                continue

        if ret.exception:
            logger_func = logger.error
        else:
            logger_func = logger.info
        logger_func('process %s:%s %s -> [%d] len:%d -> result:%.10r fol:%d msg:%d err:%r' % (
            task['project'], task['taskid'],
            task.get('url'), response.status_code, len(response.content),
            ret.result, len(ret.follows), len(ret.messages), ret.exception))
        return True

    def quit(self):
        '''Set quit signal'''
        self._quit = True

    def run(self):
        '''Run loop'''
        logger.info("processor starting...")

        while not self._quit:
            try:
                task, response = self.inqueue.get(timeout=1)
                self.on_task(task, response)
                self._exceptions = 0
            except Queue.Empty as e:
                continue
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception(e)
                self._exceptions += 1
                if self._exceptions > self.EXCEPTION_LIMIT:
                    break
                continue

        logger.info("processor exiting...")
