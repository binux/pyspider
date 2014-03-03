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
from libs import counter
logger = logging.getLogger('scheduler')


class Scheduler(object):
    _update_project_interval = 5*60
    default_schedule = {
            'priority': 0,
            'retries': 3,
            'exetime': 0,
            'age': 30*24*60*60,
            'itag': None,
            }
    LOOP_LIMIT = 1000
    
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

        self._cnt = {
                "5m": counter.CounterManager(
                    lambda : counter.TimebaseAverageWindowCounter(30, 10)),
                "1h": counter.CounterManager(
                    lambda : counter.TimebaseAverageWindowCounter(60, 60)),
                "1d": counter.CounterManager(
                    lambda : counter.TimebaseAverageWindowCounter(10*60, 24*6)),
                "all": counter.CounterManager(
                    lambda : counter.TotalCounter()),
                }
        self._cnt['1h'].load('.scheduler.1h')
        self._cnt['1d'].load('.scheduler.1d')
        self._cnt['all'].load('.scheduler.all')
        self._last_dump_cnt = 0

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
            _schedule = task.get('schedule', self.default_schedule)
            priority = _schedule.get('priority', self.default_schedule['priority'])
            exetime = _schedule.get('exetime', self.default_schedule['exetime'])
            self.task_queue.put(taskid, priority, exetime)

    def task_verify(self, task):
        for each in ('taskid', 'project', 'url', ):
            if each not in task:
                logger.error('each not in task: %s' % unicode(task[:200]))
                return False
        return True

    def insert_task(self, task):
        return self.taskdb.insert(task['project'], task['taskid'], task)

    def update_task(self, task):
        return self.taskdb.update(task['project'], task['taskid'], task)

    def put_task(self, task):
        _schedule = task.get('schedule', self.default_schedule)
        self.task_queue[task['project']].put(task['taskid'],
                priority=_schedule.get('priority', self.default_schedule['priority']),
                exetime=_schedule.get('exetime', self.default_schedule['exetime']))

    def send_task(self, task):
        self.out_fifo.put(task)

    def _check_task_done(self):
        cnt = 0
        try:
            while cnt < self.LOOP_LIMIT:
                task = self.status_fifo.get_nowait()
                if not self.task_verify(task):
                    continue
                self.task_queue[task['project']].done(task['taskid'])
                task = self.on_task_status(task)
                cnt += 1
        except Queue.Empty:
            pass
        return cnt

    merge_task_fields = ['taskid', 'project', 'url', 'status', 'schedule', 'lastcrawltime']
    def _check_request(self):
        cnt = 0
        try:
            while cnt < self.LOOP_LIMIT:
                task = self.request_fifo.get_nowait()
                if not self.task_verify(task):
                    continue
                oldtask = self.taskdb.get_task(task['project'], task['taskid'],
                        self.merge_task_fields)
                if oldtask:
                    task = self.on_old_request(task, oldtask)
                else:
                    task = self.on_new_request(task)
                cnt += 1
        except Queue.Empty:
            pass
        return cnt

    def _check_select(self):
        cnt_dict = dict()
        for project, task_queue in self.task_queue.iteritems():
            self.task_queue[project].check_update()
            cnt = 0
            taskid = task_queue.get()
            while taskid and cnt < self.LOOP_LIMIT / 10:
                task = self.taskdb.get_task(project, taskid, fields=self.request_task_fields)
                task = self.on_select_task(task)
                taskid = task_queue.get()
                cnt += 1
            cnt_dict[project] = cnt
        return cnt_dict

    def _dump_cnt(self):
        self._cnt['1h'].dump('.scheduler.1h')
        self._cnt['1d'].dump('.scheduler.1d')
        self._cnt['all'].dump('.scheduler.all')

    def _try_dump_cnt(self):
        now = time.time()
        if now - self._last_dump_cnt > 60:
            self._last_dump_cnt = now
            self._dump_cnt()

    def __len__(self):
        return sum((len(x) for x in self.task_queue.itervalues()))

    def quit(self):
        self._quit = True

    def run(self):
        logger.info("loading projects")
        self._load_projects()
        for i, project in enumerate(self.projects.keys()):
            logger.info("loading tasks from %s -- %d/%d" % (
                project, i+1, len(self.projects)))
            self._load_tasks(project)
            self.task_queue[project].rate = self.projects[project]['rate']
            self.task_queue[project].burst = self.projects[project]['burst']

        while not self._quit:
            self._update_projects()
            self._check_task_done()
            self._check_request()
            self._check_select()
            time.sleep(0.01)

        self._dump_cnt()

    def xmlrpc_run(self, port=23333, bind='127.0.0.1'):
        from SimpleXMLRPCServer import SimpleXMLRPCServer

        server = SimpleXMLRPCServer((bind, port), allow_none=True)
        server.register_introspection_functions()
        server.register_multicall_functions()

        server.register_function(self.quit, '_quit')
        server.register_function(self.__len__, 'size')
        def dump_counter(_time, _type):
            return self._cnt[_time].to_dict(_type)
        server.register_function(dump_counter, 'counter')

        server.serve_forever()
    
    def on_new_request(self, task):
        task['status'] = self.taskdb.ACTIVE
        self.insert_task(task)
        self.put_task(task)

        project = task['project']
        self._cnt['5m'].event((project, 'pending'), +1)
        self._cnt['1h'].event((project, 'pending'), +1)
        self._cnt['1d'].event((project, 'pending'), +1)
        self._cnt['all'].event((project, 'task'), +1).event((project, 'pending'), +1)
        logger.debug('new task %(project)s:%(taskid)s %(url)s' % task)
        return task

    def on_old_request(self, task, old_task):
        now = time.time()
        if old_task['status'] == self.taskdb.ACTIVE:
            logger.info('ignore newtask %(project)s:%(taskid)s %(url)s' % task)
            return None

        _schedule = task.get('schedule', self.default_schedule)
        old_schedule = old_task.get('schedule', {})

        restart = False
        if _schedule.get('itag') and _schedule['itag'] != old_schedule.get('itag'):
            restart = True
        elif _schedule['age'] + old_task['lastcrawltime'] < now:
            restart = True

        if not restart:
            logger.info('ignore newtask %(project)s:%(taskid)s %(url)s' % task)

        task['status'] = self.taskdb.ACTIVE
        self.update_task(task)
        self.put_task(task)

        project = task['project']
        self._cnt['5m'].event((project, 'pending'), +1)
        self._cnt['1h'].event((project, 'pending'), +1)
        self._cnt['1d'].event((project, 'pending'), +1)
        if old_task['status'] == self.taskdb.SUCCESS:
            self._cnt['all'].event((project, 'success'), -1).event((project, 'pending'), +1)
        elif old_task['status'] == self.taskdb.FAILED:
            self._cnt['all'].event((project, 'failed'), -1).event((project, 'pending'), +1)
        logger.debug('restart task %(project)s:%(taskid)s %(url)s' % task)
        return task

    def on_task_status(self, task):
        if 'track' not in task:
            return None
        try:
            fetchok = task['track']['fetch']['ok']
            procesok = task['track']['process']['ok']
        except KeyError, e:
            logger.error(e)
            return None

        if fetchok and procesok:
            return self.on_task_done(task)
        else:
            return self.on_task_failed(task)

    def on_task_done(self, task):
        '''
        called by task_status
        '''
        task['status'] = self.taskdb.SUCCESS
        self.update_task(task)

        project = task['project']
        self._cnt['5m'].event((project, 'success'), +1)
        self._cnt['1h'].event((project, 'success'), +1)
        self._cnt['1d'].event((project, 'success'), +1)
        self._cnt['all'].event((project, 'success'), +1).event((project, 'pending'), -1)
        logger.debug('task done %(project)s:%(taskid)s %(url)s' % task)
        return task

    def on_task_failed(self, task):
        '''
        called by task_status
        '''
        old_task = self.taskdb.get_task(task['project'], task['taskid'], fields=['schedule'])
        if not task.get('schedule'):
            task['schedule'] = old_task.get('schedule', {})

        retries = task['schedule'].get('retries', self.default_schedule['retries'])
        retried = task['schedule'].get('retried', 0)
        if retried == 0:
            next_exetime = 0
        elif retried == 1:
            next_exetime = 1 * 60 * 60
        else:
            next_exetime = 6 * (2**retried) * 60 * 60

        if retried >= retries:
            task['status'] = self.taskdb.FAILED
            self.update_task(task)

            project = task['project']
            self._cnt['5m'].event((project, 'failed'), +1)
            self._cnt['1h'].event((project, 'failed'), +1)
            self._cnt['1d'].event((project, 'failed'), +1)
            self._cnt['all'].event((project, 'failed'), +1).event((project, 'pending'), -1)
            logger.info('task failed %(project)s:%(taskid)s %(url)s' % task)
            return task
        else:
            task['schedule']['retried'] = retried + 1
            task['schedule']['exetime'] = time.time() + next_exetime
            self.update_task(task)
            self.put_task(task)

            project = task['project']
            self._cnt['5m'].event((project, 'retry'), +1)
            self._cnt['1h'].event((project, 'retry'), +1)
            self._cnt['1d'].event((project, 'retry'), +1)
            logger.info('task retry %(project)s:%(taskid)s %(url)s' % task)
            return task
        
    def on_select_task(self, task):
        logger.debug('select %(project)s:%(taskid)s %(url)s' % task)
        self.send_task(task)
        return task
