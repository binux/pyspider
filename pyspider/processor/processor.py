#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 22:59:56

import sys
import time
import logging
logger = logging.getLogger("processor")

from six.moves import queue as Queue
from pyspider.libs import utils
from pyspider.libs.response import rebuild_response
from .project_module import ProjectManager, ProjectLoader, ProjectFinder


class Processor(object):
    PROCESS_TIME_LIMIT = 30
    EXCEPTION_LIMIT = 3

    RESULT_LOGS_LIMIT = 1000
    RESULT_RESULT_LIMIT = 10

    def __init__(self, projectdb, inqueue, status_queue, newtask_queue, result_queue,
                 enable_stdout_capture=True,
                 enable_projects_import=True):
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
        ))

        if enable_projects_import:
            self.enable_projects_import()

    def enable_projects_import(self):
        '''
        Enable import other project as module

        `from project import project_name`
        '''
        _self = self

        class ProcessProjectFinder(ProjectFinder):

            def get_loader(self, name):
                info = _self.projectdb.get(name)
                if info:
                    return ProjectLoader(info)
        sys.meta_path.append(ProcessProjectFinder())

    def __del__(self):
        pass

    def on_task(self, task, response):
        '''Deal one task'''
        start_time = time.time()
        try:
            response = rebuild_response(response)
            assert 'taskid' in task, 'need taskid in task'
            project = task['project']
            updatetime = task.get('updatetime', None)
            project_data = self.project_manager.get(project, updatetime)
            if not project_data:
                logger.error("no such project: %s", project)
                return False
            ret = project_data['instance'].run_task(
                project_data['module'], task, response)
        except Exception as e:
            logger.exception(e)
            return False
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
                        'encoding': response.encoding,
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
                },
            }

            # FIXME: unicode_obj should used in scheduler before store to database
            # it's used here for performance.
            self.status_queue.put(utils.unicode_obj(status_pack))

        # FIXME: unicode_obj should used in scheduler before store to database
        # it's used here for performance.
        if ret.follows:
            self.newtask_queue.put([utils.unicode_obj(newtask) for newtask in ret.follows])

        for project, msg, url in ret.messages:
            self.inqueue.put(({
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
            }))

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
