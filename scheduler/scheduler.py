#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-07 17:05:11


import time
import Queue
import logging
from task_queue import TaskQueue


class Scheduler(object):
    _update_project_interval = 5*60
    
    def __init__(self, taskdb, projectdb, request_fifo, status_fifo, out_fifo):
        self.taskdb = taskdb
        self.projectdb = projectdb
        self.request_fifo = request_fifo
        self.status_fifo = status_fifo
        self.out_fifo = out_fifo

        self._quit = False
        self.projects = dict()
        self._last_update_project = 0
        self.task_queue = dict()

    def _load_projects(self):
        self.projects = dict()
        for project in self.projectdb.get_all():
            self.projects[project['name']] = project
        self._last_update_project = time.time()

    def _update_projects(self):
        now = time.time()
        if self._last_update_project + self._update_project_interval > now:
            return
        for project in self.projectdb.check_update(now):
            self.projects[project['name']] = project
            if project['name'] not in self.task_queue:
                self._load_tasks(project['name'])
            self.task_queue[project['name']].rate = project['rate']
            self.task_queue[project['name']].burst = project['burst']

    scheduler_task_fields = ['taskid', 'project', 'schedule', ]
    def _load_tasks(self, project):
        self.task_queue[project] = TaskQueue(rate=0, burst=0)
        for task in self.taskdb.load_tasks('ACTIVE', project,
                self.scheduler_task_fields):
            taskid = task['taskid']
            if 'schedule' in task:
                priority = task['schedule'].get('priority', 0)
                exetime = task['schedule'].get('exetime', 0)
            else:
                priority = 0
                exetime = 0
            self.task_queue.put(taskid, priority, exetime)

    request_task_fields = ['taskid', 'project', 'fetch', 'process']
    def _load_task_body(self, taskid):
        return self.taskdb.get_task(taskid, fields=self.request_task_fields)

    def _insert_task(self, task):
        return self.taskdb.insert(task['project'], task['taskid'], task)

    def _update_task(self, task):
        return self.taskdb.insert(task['project'], task['taskid'], task)

    def _check_task_done(self):
        cnt = 0
        try:
            while True:
                task = self.status_fifo.get_nowait()
                if 'taskid' not in task:
                    logging.error("taskid not in task: %s", task)
                    continue
                if 'project' not in task:
                    logging.error("project not in task: %s", task)
                    continue
                task = self.on_task_status(task)
                if task:
                    self._update_task(task)
                    self.task_queue[task['project']].done(task['taskid'])
                cnt += 1
        except Queue.Empty:
            pass
        return cnt

    merge_task_fields = ['taskid', 'project', 'fetch', 'process']
    def _check_request(self):
        cnt = 0
        try:
            while True:
                task = self.request_fifo.get_nowait()
                if 'taskid' not in task:
                    logging.error("taskid not in task: %s", task)
                    continue
                if 'project' not in task:
                    logging.error("project not in task: %s", task)
                    continue
                oldtask = self.taskdb.get_task(task['project'], task['taskid'],
                        self.merge_task_fields)
                if oldtask:
                    task = self.on_old_request(task, oldtask)
                    self._update_task(task)
                else:
                    task = self.on_new_request(task)
                    self._insert_task(task)
                if task:
                    self.task_queue[task['project']].put(task['taskid'],
                            priority=task.get('priority', 0),
                            exetime=task.get('exetime', 0))
                cnt += 1
        except Queue.Empty:
            pass
        return cnt

    def _check_select(self):
        cnt_dict = dict()
        for project, task_queue in self.task_queue.iteritems():
            cnt = 0
            taskid = task_queue.get()
            while taskid:
                task = self._load_task_body(taskid)
                task = self.on_select_task(task)
                if task:
                    self.out_fifo.put(task)
                taskid = task_queue.get()
                cnt += 1
            cnt_dict[project] = cnt
        return cnt_dict

    def __len__(self):
        return sum((len(x) for x in self.task_queue.itervalues()))

    def quit(self):
        self._quit = True

    def run(self):
        logging.info("loading projects")
        self._load_projects()
        for i, project in enumerate(self.projects.keys()):
            logging.info("loading tasks from %s -- %d/%d" % (
                project, i+1, len(self.projects)))
            self._load_tasks(project)
            self.task_queue[project].rate = self.projects[project]['rate']
            self.task_queue[project].burst = self.projects[project]['burst']
        while not self._quit:
            self._update_projects()
            self._check_task_done()
            self._check_request()
            self._check_select()
            time.sleep(0.1)

    def on_new_request(self, task):
        pass

    def on_old_request(self, task, old_task):
        pass

    def on_task_status(self, task):
        return task

    def on_task_done(self, task):
        '''
        called by task_status
        '''
        pass

    def on_task_failed(self, task):
        '''
        called by task_status
        '''
        pass

    def on_select_task(self, task):
        return task
