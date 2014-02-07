#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-07 17:05:11


import Queue
import logging
from task_queue import TaskQueue


class Scheduler(object):
    def __init__(self, taskdb, projectdb, request_fifo, status_fifo, out_fifo):
        self.taskdb = taskdb
        self.projectdb = projectdb
        self.request_fifo = request_fifo
        self.status_fifo = status_fifo
        self.out_fifo = out_fifo

        self._quit = False
        self.task_queue = dict()

    def _load_projects(self):
        pass

    def _load_tasks(self, project):
        pass

    def _load_task_body(self, taskid):
        pass

    def _save_task(self, task):
        pass

    def _save_task_status(self, task):
        pass

    def _update_projects(self):
        pass

    def _check_task_done(self):
        cnt = 0
        try:
            while True:
                task = self.status_fifo.get_nowait()
                if 'taskid' not in task:
                    logging.error("taskid not in task: %s", task)
                    continue
                task = self.on_task_status(task)
                if task:
                    self._save_task_status(task)
                    self.task_queue.done(task['taskid'])
                cnt += 1
        except Queue.Empty:
            pass
        return cnt

    def _check_request(self):
        cnt = 0
        try:
            while True:
                task = self.request_fifo.get_nowait()
                if 'taskid' not in task:
                    logging.error("taskid not in task: %s", task)
                    continue
                task = self.on_request(task)
                if task:
                    self._save_task(task)
                    self.task_queue.put(task['taskid'],
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
        logging.info("loading tasks")
        self._load_tasks()
        while not self._quit:
            self._update_projects()
            self._check_task_done()
            self._check_request()
            self._check_select()
            time.sleep(0.1)

    def on_request(self, task):
        return task

    def on_new_request(self, task):
        '''
        called by on_request
        '''
        pass

    def on_old_request(self, task, old_task):
        '''
        called by on_request
        '''
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
