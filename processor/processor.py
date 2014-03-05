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
import project_module
from libs.response import rebuild_response
logger = logging.getLogger("processor")

def build_module(project, env={}):
    assert 'name' in project, 'need name of project'
    assert 'script' in project, 'need script of project'

    env = dict(env)
    env.update({
        'project': project,
        'debug': project.get('status', 'DEBUG') == 'DEBUG',
        })

    script = project['script']
    if isinstance(script, unicode):
        script = script.encode('utf8')

    module = project_module.ProjectModule(project['name'], script, env)
    module.rethrow()
    _class = module.get('__class__')
    assert _class is not None, "need BaseHandler in project module"
    instance = _class()._init(project)

    return {
        'module': module,
        'class': _class,
        'instance': instance,
        'info': project
        }

class Processor(object):
    CHECK_PROJECTS_INTERVAL = 5*60

    def __init__(self, projectdb, inqueue, status_queue, newtask_queue):
        self.inqueue = inqueue
        self.status_queue = status_queue
        self.newtask_queue = newtask_queue
        self.projectdb = projectdb

        self._quit = False
        self.projects = {}
        self.last_check_projects = 0

    def _init_projects(self):
        for project in self.projectdb.get_all():
            try:
                self._update_project(project)
            except Exception, e:
                logger.exception("exception when init projects for %s" % project.get('name', None))
                continue
        self.last_check_projects = time.time()

    def _check_projects(self):
        if time.time() - self.last_check_projects < self.CHECK_PROJECTS_INTERVAL:
            return
        for project in self.projectdb.check_update(self.last_check_projects):
            try:
                self._update_project(project)
            except Exception, e:
                logger.exception("exception when check update for %s" % project.get('name', None))
                continue
        self.last_check_projects = time.time()

    def _update_project(self, project):
        self.projects[project['name']] = build_module(project)

    def on_task(self, task, response):
        start_time = time.time()
        try:
            response = rebuild_response(response)
            assert 'taskid' in task, 'need taskid in task'
            project = task['project']
            if project not in self.projects:
                raise LookupError("not such project: %s" % project)
            project_data = self.projects[project]
            ret = project_data['instance'].run(project_data['module'], task, response)
        except Exception, e:
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
                            'ok': not response.error,
                            'time': response.time,
                            'status_code': response.status_code,
                            'headers': dict(response.headers),
                            'encoding': response.encoding,
                            #'content': response.content,
                            },
                        'process': {
                            'ok': not ret.exception,
                            'time': process_time,
                            'follows': len(ret.follows),
                            'result': unicode(ret.result)[:100],
                            'logs': ret.logstr()[:200],
                            'exception': unicode(ret.exception),
                            }
                        }
                    }
            self.status_queue.put(status_pack)

        for task in ret.follows:
            self.newtask_queue.put(task)

        #TODO: do with messages
        return True

    def run(self):
        while not self._quit:
            try:
                self._check_projects()
            except Exception, e:
                logger.exception(e)

            try:
                task, response = self.inqueue.get()
                self.on_task(task, response)
            except Queue.Empty, e:
                time.sleep(1)
                continue
            except Exception, e:
                logger.exception(e)
                continue
