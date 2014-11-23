#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-16 22:59:56

import sys
import time
import Queue
import logging
from pyspider.libs import utils
from pyspider.libs.response import rebuild_response
from project_module import ProjectLoader, ProjectFinder
logger = logging.getLogger("processor")


def build_module(project, env={}):
    assert 'name' in project, 'need name of project'
    assert 'script' in project, 'need script of project'

    # fix for old non-package version scripts
    if 'pyspider' not in sys.path:
        sys.path.insert(1, 'pyspider')

    env = dict(env)
    env.update({
        'debug': project.get('status', 'DEBUG') == 'DEBUG',
    })

    loader = ProjectLoader(project)
    module = loader.load_module(project['name'])
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
        'info': project
    }


class Processor(object):
    PROCESS_TIME_LIMIT = 30
    CHECK_PROJECTS_INTERVAL = 5 * 60
    EXCEPTION_LIMIT = 3

    RESULT_LOGS_LIMIT = 1000
    RESULT_RESULT_LIMIT = 100

    def __init__(self, projectdb, inqueue, status_queue, newtask_queue, result_queue):
        self.inqueue = inqueue
        self.status_queue = status_queue
        self.newtask_queue = newtask_queue
        self.result_queue = result_queue
        self.projectdb = projectdb

        self._quit = False
        self._exceptions = 10
        self.projects = {}
        self.last_check_projects = 0

        self.enable_projects_import()

    def enable_projects_import(self):
        _self = self

        class ProcessProjectFinder(ProjectFinder):

            def get_loader(self, name):
                info = _self.projectdb.get(name)
                if info:
                    return ProjectLoader(info)
        sys.meta_path.append(ProcessProjectFinder())

    def __del__(self):
        reload(__builtin__)

    def _init_projects(self):
        for project in self.projectdb.get_all():
            try:
                self._update_project(project)
            except Exception:
                logger.exception("exception when init projects for %s" % project.get('name', None))
                continue
        self.last_check_projects = time.time()

    def _need_update(self, task):
        if task['project'] not in self.projects:
            return True
        if (
                task.get('project_updatetime', 0)
                >
                self.projects[task['project']]['info'].get('updatetime', 0)
        ):
            return True
        if time.time() - self.last_check_projects < self.CHECK_PROJECTS_INTERVAL:
            return True
        return False

    def _check_projects(self, task):
        if not self._need_update(task):
            return
        for project in self.projectdb.check_update(self.last_check_projects):
            try:
                logger.debug("project: %s updated." % project['name'])
                self._update_project(project)
            except Exception:
                logger.exception("exception when check update for %s" % project.get('name', None))
                continue
        self.last_check_projects = time.time()

    def _update_project(self, project):
        self.projects[project['name']] = build_module(project, dict(
            result_queue=self.result_queue))

    def on_task(self, task, response):
        start_time = time.time()
        try:
            response = rebuild_response(response)
            assert 'taskid' in task, 'need taskid in task'
            project = task['project']
            if project not in self.projects:
                raise LookupError("no such project: %s" % project)
            project_data = self.projects[project]
            ret = project_data['instance'].run(
                project_data['module'], task, response)
        except Exception as e:
            logger.exception(e)
            return False
        process_time = time.time() - start_time

        if not ret.extinfo.get('not_send_status', False):
            status_pack = {
                'taskid': task['taskid'],
                'project': task['project'],
                'url': task.get('url'),
                'track': {
                    'fetch': {
                        'ok': response.isok(),
                        'time': response.time,
                        'status_code': response.status_code,
                        'headers': dict(response.headers),
                        'encoding': response.encoding,
                        'content': (
                            response.content[:500]
                            if not response.isok() or ret.exception else
                            None
                        ),
                    },
                    'process': {
                        'ok': not ret.exception,
                        'time': process_time,
                        'follows': len(ret.follows),
                        'result': unicode(ret.result)[:self.RESULT_RESULT_LIMIT],
                        'logs': ret.logstr()[-self.RESULT_LOGS_LIMIT:],
                        'exception': ret.exception,
                    },
                },
            }

            # FIXME: unicode_obj should used in scheduler before store to database
            # it's used here for performance.
            self.status_queue.put(utils.unicode_obj(status_pack))

        for newtask in ret.follows:
            # FIXME: unicode_obj should used in scheduler before store to database
            # it's used here for performance.
            self.newtask_queue.put(utils.unicode_obj(newtask))

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

        if response.error or ret.exception:
            logger_func = logger.error
        else:
            logger_func = logger.info
        logger_func('process %s:%s %s -> [%d] len:%d -> result:%.10r fol:%d msg:%d err:%r' % (
            task['project'], task['taskid'],
            task.get('url'), response.status_code, len(response.content),
            ret.result, len(ret.follows), len(ret.messages), ret.exception))
        return True

    def quit(self):
        self._quit = True

    def run(self):
        while not self._quit:
            try:
                task, response = self.inqueue.get(timeout=1)
                self._check_projects(task)
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
