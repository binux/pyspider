#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-07 17:05:11


import os
import json
import time
import logging
import itertools
from collections import deque

from six import iteritems, itervalues

from pyspider.libs import counter, utils
from six.moves import queue as Queue
from .task_queue import TaskQueue
logger = logging.getLogger('scheduler')


class Scheduler(object):
    UPDATE_PROJECT_INTERVAL = 5 * 60
    default_schedule = {
        'priority': 0,
        'retries': 3,
        'exetime': 0,
        'age': -1,
        'itag': None,
    }
    LOOP_LIMIT = 1000
    LOOP_INTERVAL = 0.1
    ACTIVE_TASKS = 100
    INQUEUE_LIMIT = 0
    EXCEPTION_LIMIT = 3
    DELETE_TIME = 24 * 60 * 60
    DEFAULT_RETRY_DELAY = {
        0: 30,
        1: 1*60*60,
        2: 6*60*60,
        3: 12*60*60,
        '': 24*60*60
    }

    def __init__(self, taskdb, projectdb, newtask_queue, status_queue,
                 out_queue, data_path='./data', resultdb=None):
        self.taskdb = taskdb
        self.projectdb = projectdb
        self.resultdb = resultdb
        self.newtask_queue = newtask_queue
        self.status_queue = status_queue
        self.out_queue = out_queue
        self.data_path = data_path

        self._send_buffer = deque()
        self._quit = False
        self._exceptions = 0
        self.projects = dict()
        self._force_update_project = False
        self._last_update_project = 0
        self.task_queue = dict()
        self._last_tick = int(time.time())

        self._cnt = {
            "5m_time": counter.CounterManager(
                lambda: counter.TimebaseAverageEventCounter(30, 10)),
            "5m": counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(30, 10)),
            "1h": counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(60, 60)),
            "1d": counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(10 * 60, 24 * 6)),
            "all": counter.CounterManager(
                lambda: counter.TotalCounter()),
        }
        self._cnt['1h'].load(os.path.join(self.data_path, 'scheduler.1h'))
        self._cnt['1d'].load(os.path.join(self.data_path, 'scheduler.1d'))
        self._cnt['all'].load(os.path.join(self.data_path, 'scheduler.all'))
        self._last_dump_cnt = 0

    def _update_projects(self):
        '''Check project update'''
        now = time.time()
        if (
                not self._force_update_project
                and self._last_update_project + self.UPDATE_PROJECT_INTERVAL > now
        ):
            return
        for project in self.projectdb.check_update(self._last_update_project):
            self._update_project(project)
            logger.debug("project: %s updated.", project['name'])
        self._force_update_project = False
        self._last_update_project = now

    def _update_project(self, project):
        '''update one project'''
        if project['name'] not in self.projects:
            self.projects[project['name']] = {}
        self.projects[project['name']].update(project)
        self.projects[project['name']]['md5sum'] = utils.md5string(project['script'])
        if not self.projects[project['name']].get('active_tasks', None):
            self.projects[project['name']]['active_tasks'] = deque(maxlen=self.ACTIVE_TASKS)

        # load task queue when project is running and delete task_queue when project is stoped
        if project['status'] in ('RUNNING', 'DEBUG'):
            if project['name'] not in self.task_queue:
                self._load_tasks(project['name'])
            self.task_queue[project['name']].rate = project['rate']
            self.task_queue[project['name']].burst = project['burst']

            # update project runtime info from processor by sending a _on_get_info
            # request, result is in status_page.track.save
            self.on_select_task({
                'taskid': '_on_get_info',
                'project': project['name'],
                'url': 'data:,_on_get_info',
                'status': self.taskdb.SUCCESS,
                'fetch': {
                    'save': ['min_tick', 'retry_delay'],
                },
                'process': {
                    'callback': '_on_get_info',
                },
            })
        else:
            if project['name'] in self.task_queue:
                self.task_queue[project['name']].rate = 0
                self.task_queue[project['name']].burst = 0
                del self.task_queue[project['name']]

            if project not in self._cnt['all']:
                self._update_project_cnt(project['name'])

    scheduler_task_fields = ['taskid', 'project', 'schedule', ]

    def _load_tasks(self, project):
        '''load tasks from database'''
        self.task_queue[project] = TaskQueue(rate=0, burst=0)
        for task in self.taskdb.load_tasks(
                self.taskdb.ACTIVE, project, self.scheduler_task_fields
        ):
            taskid = task['taskid']
            _schedule = task.get('schedule', self.default_schedule)
            priority = _schedule.get('priority', self.default_schedule['priority'])
            exetime = _schedule.get('exetime', self.default_schedule['exetime'])
            self.task_queue[project].put(taskid, priority, exetime)
        logger.debug('project: %s loaded %d tasks.', project, len(self.task_queue[project]))

        if self.projects[project]['status'] in ('RUNNING', 'DEBUG'):
            self.task_queue[project].rate = self.projects[project]['rate']
            self.task_queue[project].burst = self.projects[project]['burst']
        else:
            self.task_queue[project].rate = 0
            self.task_queue[project].burst = 0

        if project not in self._cnt['all']:
            self._update_project_cnt(project)
        self._cnt['all'].value((project, 'pending'), len(self.task_queue[project]))

    def _update_project_cnt(self, project):
        status_count = self.taskdb.status_count(project)
        self._cnt['all'].value(
            (project, 'success'),
            status_count.get(self.taskdb.SUCCESS, 0)
        )
        self._cnt['all'].value(
            (project, 'failed'),
            status_count.get(self.taskdb.FAILED, 0) + status_count.get(self.taskdb.BAD, 0)
        )
        self._cnt['all'].value(
            (project, 'pending'),
            status_count.get(self.taskdb.ACTIVE, 0)
        )

    def task_verify(self, task):
        '''
        return False if any of 'taskid', 'project', 'url' is not in task dict
                        or project in not in task_queue
        '''
        for each in ('taskid', 'project', 'url', ):
            if each not in task or not task[each]:
                logger.error('%s not in task: %.200r', each, task)
                return False
        if task['project'] not in self.task_queue:
            logger.error('unknown project: %s', task['project'])
            return False
        return True

    def insert_task(self, task):
        '''insert task into database'''
        return self.taskdb.insert(task['project'], task['taskid'], task)

    def update_task(self, task):
        '''update task in database'''
        return self.taskdb.update(task['project'], task['taskid'], task)

    def put_task(self, task):
        '''put task to task queue'''
        _schedule = task.get('schedule', self.default_schedule)
        self.task_queue[task['project']].put(
            task['taskid'],
            priority=_schedule.get('priority', self.default_schedule['priority']),
            exetime=_schedule.get('exetime', self.default_schedule['exetime'])
        )

    def send_task(self, task, force=True):
        '''
        dispatch task to fetcher

        out queue may have size limit to prevent block, a send_buffer is used
        '''
        try:
            self.out_queue.put_nowait(task)
        except Queue.Full:
            if force:
                self._send_buffer.appendleft(task)
            else:
                raise

    def _check_task_done(self):
        '''Check status queue'''
        cnt = 0
        try:
            while True:
                task = self.status_queue.get_nowait()
                # check _on_get_info result here
                if task.get('taskid') == '_on_get_info' and 'project' in task and 'track' in task:
                    self.projects[task['project']].update(task['track'].get('save') or {})
                    logger.info(
                        '%s on_get_info %r', task['project'], task['track'].get('save', {})
                    )
                    continue
                elif not self.task_verify(task):
                    continue
                self.on_task_status(task)
                cnt += 1
        except Queue.Empty:
            pass
        return cnt

    merge_task_fields = ['taskid', 'project', 'url', 'status', 'schedule', 'lastcrawltime']

    def _check_request(self):
        '''Check new task queue'''
        tasks = {}
        while len(tasks) < self.LOOP_LIMIT:
            try:
                task = self.newtask_queue.get_nowait()
            except Queue.Empty:
                break

            if isinstance(task, list):
                _tasks = task
            else:
                _tasks = (task, )

            for task in _tasks:
                if not self.task_verify(task):
                    continue

                if task['taskid'] in self.task_queue[task['project']]:
                    if not task.get('schedule', {}).get('force_update', False):
                        logger.debug('ignore newtask %(project)s:%(taskid)s %(url)s', task)
                        continue

                if task['taskid'] in tasks:
                    if not task.get('schedule', {}).get('force_update', False):
                        continue

                tasks[task['taskid']] = task

        for task in itervalues(tasks):
            self.on_request(task)

        return len(tasks)

    def _check_cronjob(self):
        """Check projects cronjob tick, return True when a new tick is sended"""
        now = time.time()
        self._last_tick = int(self._last_tick)
        if now - self._last_tick < 1:
            return False
        self._last_tick += 1
        for project in itervalues(self.projects):
            if project['status'] not in ('DEBUG', 'RUNNING'):
                continue
            if project.get('min_tick', 0) == 0:
                continue
            if self._last_tick % int(project['min_tick']) != 0:
                continue
            self.on_select_task({
                'taskid': '_on_cronjob',
                'project': project['name'],
                'url': 'data:,_on_cronjob',
                'status': self.taskdb.SUCCESS,
                'fetch': {
                    'save': {
                        'tick': self._last_tick,
                    },
                },
                'process': {
                    'callback': '_on_cronjob',
                },
            })
        return True

    request_task_fields = [
        'taskid',
        'project',
        'url',
        'status',
        'schedule',
        'fetch',
        'process',
        'track',
        'lastcrawltime'
    ]

    def _check_select(self):
        '''Select task to fetch & process'''
        while self._send_buffer:
            _task = self._send_buffer.pop()
            try:
                # use force=False here to prevent automatic send_buffer append and get exception
                self.send_task(_task, False)
            except Queue.Full:
                self._send_buffer.append(_task)
                break

        if self.out_queue.full():
            return {}

        taskids = []
        cnt = 0
        cnt_dict = dict()
        limit = self.LOOP_LIMIT
        for project, task_queue in iteritems(self.task_queue):
            if cnt >= limit:
                break

            # task queue
            self.task_queue[project].check_update()
            project_cnt = 0

            # check send_buffer here. when not empty, out_queue may blocked. Not sending tasks
            while cnt < limit and project_cnt < limit / 10:
                taskid = task_queue.get()
                if not taskid:
                    break

                taskids.append((project, taskid))
                project_cnt += 1
                cnt += 1
            cnt_dict[project] = project_cnt

        for project, taskid in taskids:
            self._load_put_task(project, taskid)

        return cnt_dict

    def _load_put_task(self, project, taskid):
        task = self.taskdb.get_task(project, taskid, fields=self.request_task_fields)
        if not task:
            return
        task = self.on_select_task(task)

    def _print_counter_log(self):
        # print top 5 active counters
        keywords = ('pending', 'success', 'retry', 'failed')
        total_cnt = {}
        project_actives = []
        project_fails = []
        for key in keywords:
            total_cnt[key] = 0
        for project, subcounter in iteritems(self._cnt['5m']):
            actives = 0
            for key in keywords:
                cnt = subcounter.get(key, None)
                if cnt:
                    cnt = cnt.sum
                    total_cnt[key] += cnt
                    actives += cnt

            project_actives.append((actives, project))

            fails = subcounter.get('failed', None)
            if fails:
                project_fails.append((fails.sum, project))

        top_2_fails = sorted(project_fails, reverse=True)[:2]
        top_3_actives = sorted([x for x in project_actives if x[1] not in top_2_fails],
                               reverse=True)[:5 - len(top_2_fails)]

        log_str = ("in 5m: new:%(pending)d,success:%(success)d,"
                   "retry:%(retry)d,failed:%(failed)d" % total_cnt)
        for _, project in itertools.chain(top_3_actives, top_2_fails):
            subcounter = self._cnt['5m'][project].to_dict(get_value='sum')
            log_str += " %s:%d,%d,%d,%d" % (project,
                                            subcounter.get('pending', 0),
                                            subcounter.get('success', 0),
                                            subcounter.get('retry', 0),
                                            subcounter.get('failed', 0))
        logger.info(log_str)

    def _dump_cnt(self):
        '''Dump counters to file'''
        self._cnt['1h'].dump(os.path.join(self.data_path, 'scheduler.1h'))
        self._cnt['1d'].dump(os.path.join(self.data_path, 'scheduler.1d'))
        self._cnt['all'].dump(os.path.join(self.data_path, 'scheduler.all'))

    def _try_dump_cnt(self):
        '''Dump counters every 60 seconds'''
        now = time.time()
        if now - self._last_dump_cnt > 60:
            self._last_dump_cnt = now
            self._dump_cnt()
            self._print_counter_log()

    def _check_delete(self):
        '''Check project delete'''
        now = time.time()
        for project in list(itervalues(self.projects)):
            if project['status'] != 'STOP':
                continue
            if now - project['updatetime'] < self.DELETE_TIME:
                continue
            if 'delete' not in self.projectdb.split_group(project['group']):
                continue

            logger.warning("deleting project: %s!", project['name'])
            if project['name'] in self.task_queue:
                self.task_queue[project['name']].rate = 0
                self.task_queue[project['name']].burst = 0
                del self.task_queue[project['name']]
            del self.projects[project['name']]
            self.taskdb.drop(project['name'])
            self.projectdb.drop(project['name'])
            if self.resultdb:
                self.resultdb.drop(project['name'])

    def __len__(self):
        return sum(len(x) for x in itervalues(self.task_queue))

    def quit(self):
        '''Set quit signal'''
        self._quit = True

    def run_once(self):
        '''comsume queues and feed tasks to fetcher, once'''

        self._update_projects()
        self._check_task_done()
        self._check_request()
        while self._check_cronjob():
            pass
        self._check_select()
        self._check_delete()
        self._try_dump_cnt()

    def run(self):
        '''Start scheduler loop'''
        logger.info("loading projects")

        while not self._quit:
            try:
                time.sleep(self.LOOP_INTERVAL)
                self.run_once()
                self._exceptions = 0
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.exception(e)
                self._exceptions += 1
                if self._exceptions > self.EXCEPTION_LIMIT:
                    break
                continue

        logger.info("scheduler exiting...")
        self._dump_cnt()

    def trigger_on_start(self, project):
        '''trigger an on_start callback of project'''
        self.newtask_queue.put({
            "project": project,
            "taskid": "on_start",
            "url": "data:,on_start",
            "process": {
                "callback": "on_start",
            },
        })

    def xmlrpc_run(self, port=23333, bind='127.0.0.1', logRequests=False):
        '''Start xmlrpc interface'''
        try:
            from six.moves.xmlrpc_server import SimpleXMLRPCServer
        except ImportError:
            from SimpleXMLRPCServer import SimpleXMLRPCServer

        server = SimpleXMLRPCServer((bind, port), allow_none=True, logRequests=logRequests)
        server.register_introspection_functions()
        server.register_multicall_functions()

        server.register_function(self.quit, '_quit')
        server.register_function(self.__len__, 'size')

        def dump_counter(_time, _type):
            try:
                return self._cnt[_time].to_dict(_type)
            except:
                logger.exception('')
        server.register_function(dump_counter, 'counter')

        def new_task(task):
            if self.task_verify(task):
                self.newtask_queue.put(task)
                return True
            return False
        server.register_function(new_task, 'newtask')

        def send_task(task):
            '''dispatch task to fetcher'''
            self.send_task(task)
            return True
        server.register_function(send_task, 'send_task')

        def update_project():
            self._force_update_project = True
        server.register_function(update_project, 'update_project')

        def get_active_tasks(project=None, limit=100):
            allowed_keys = set((
                'taskid',
                'project',
                'status',
                'url',
                'lastcrawltime',
                'updatetime',
                'track',
            ))
            track_allowed_keys = set((
                'ok',
                'time',
                'follows',
                'status_code',
            ))

            iters = [iter(x['active_tasks']) for k, x in iteritems(self.projects)
                     if x and (k == project if project else True)]
            tasks = [next(x, None) for x in iters]
            result = []

            while len(result) < limit and tasks and not all(x is None for x in tasks):
                updatetime, task = t = max(t for t in tasks if t)
                i = tasks.index(t)
                tasks[i] = next(iters[i], None)
                for key in list(task):
                    if key == 'track':
                        for k in list(task[key].get('fetch', [])):
                            if k not in track_allowed_keys:
                                del task[key]['fetch'][k]
                        for k in list(task[key].get('process', [])):
                            if k not in track_allowed_keys:
                                del task[key]['process'][k]
                    if key in allowed_keys:
                        continue
                    del task[key]
                result.append(t)
            # fix for "<type 'exceptions.TypeError'>:dictionary key must be string"
            # have no idea why
            return json.loads(json.dumps(result))
        server.register_function(get_active_tasks, 'get_active_tasks')

        server.timeout = 0.5
        while not self._quit:
            server.handle_request()
        server.server_close()

    def on_request(self, task):
        if self.INQUEUE_LIMIT and len(self.task_queue[task['project']]) >= self.INQUEUE_LIMIT:
            logger.debug('overflow task %(project)s:%(taskid)s %(url)s', task)
            return

        oldtask = self.taskdb.get_task(task['project'], task['taskid'],
                                       fields=self.merge_task_fields)
        if oldtask:
            return self.on_old_request(task, oldtask)
        else:
            return self.on_new_request(task)

    def on_new_request(self, task):
        '''Called when a new request is arrived'''
        task['status'] = self.taskdb.ACTIVE
        self.insert_task(task)
        self.put_task(task)

        project = task['project']
        self._cnt['5m'].event((project, 'pending'), +1)
        self._cnt['1h'].event((project, 'pending'), +1)
        self._cnt['1d'].event((project, 'pending'), +1)
        self._cnt['all'].event((project, 'pending'), +1)
        logger.info('new task %(project)s:%(taskid)s %(url)s', task)
        return task

    def on_old_request(self, task, old_task):
        '''Called when a crawled task is arrived'''
        now = time.time()

        _schedule = task.get('schedule', self.default_schedule)
        old_schedule = old_task.get('schedule', {})

        restart = False
        schedule_age = _schedule.get('age', self.default_schedule['age'])
        if _schedule.get('itag') and _schedule['itag'] != old_schedule.get('itag'):
            restart = True
        elif schedule_age >= 0 and schedule_age + (old_task.get('lastcrawltime', 0) or 0) < now:
            restart = True
        elif _schedule.get('force_update'):
            restart = True

        if not restart:
            logger.debug('ignore newtask %(project)s:%(taskid)s %(url)s', task)
            return

        task['status'] = self.taskdb.ACTIVE
        self.update_task(task)
        self.put_task(task)

        project = task['project']
        if old_task['status'] != self.taskdb.ACTIVE:
            self._cnt['5m'].event((project, 'pending'), +1)
            self._cnt['1h'].event((project, 'pending'), +1)
            self._cnt['1d'].event((project, 'pending'), +1)
        if old_task['status'] == self.taskdb.SUCCESS:
            self._cnt['all'].event((project, 'success'), -1).event((project, 'pending'), +1)
        elif old_task['status'] == self.taskdb.FAILED:
            self._cnt['all'].event((project, 'failed'), -1).event((project, 'pending'), +1)
        logger.info('restart task %(project)s:%(taskid)s %(url)s', task)
        return task

    def on_task_status(self, task):
        '''Called when a status pack is arrived'''
        try:
            procesok = task['track']['process']['ok']
            if not self.task_queue[task['project']].done(task['taskid']):
                logging.error('not processing pack: %(project)s:%(taskid)s %(url)s', task)
                return None
        except KeyError as e:
            logger.error("Bad status pack: %s", e)
            return None

        if procesok:
            ret = self.on_task_done(task)
        else:
            ret = self.on_task_failed(task)

        if task['track']['fetch'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'fetch_time'),
                                       task['track']['fetch']['time'])
        if task['track']['process'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'process_time'),
                                       task['track']['process'].get('time'))
        self.projects[task['project']]['active_tasks'].appendleft((time.time(), task))
        return ret

    def on_task_done(self, task):
        '''Called when a task is done and success, called by `on_task_status`'''
        task['status'] = self.taskdb.SUCCESS
        task['lastcrawltime'] = time.time()

        if 'schedule' in task:
            if task['schedule'].get('auto_recrawl') and 'age' in task['schedule']:
                task['status'] = self.taskdb.ACTIVE
                next_exetime = task['schedule'].get('age')
                task['schedule']['exetime'] = time.time() + next_exetime
                self.put_task(task)
            else:
                del task['schedule']
        self.update_task(task)

        project = task['project']
        self._cnt['5m'].event((project, 'success'), +1)
        self._cnt['1h'].event((project, 'success'), +1)
        self._cnt['1d'].event((project, 'success'), +1)
        self._cnt['all'].event((project, 'success'), +1).event((project, 'pending'), -1)
        logger.info('task done %(project)s:%(taskid)s %(url)s', task)
        return task

    def on_task_failed(self, task):
        '''Called when a task is failed, called by `on_task_status`'''

        if 'schedule' not in task:
            old_task = self.taskdb.get_task(task['project'], task['taskid'], fields=['schedule'])
            if old_task is None:
                logging.error('unknown status pack: %s' % task)
                return
            task['schedule'] = old_task.get('schedule', {})

        retries = task['schedule'].get('retries', self.default_schedule['retries'])
        retried = task['schedule'].get('retried', 0)

        project_info = self.projects.get(task['project'], {})
        retry_delay = project_info.get('retry_delay', None) or self.DEFAULT_RETRY_DELAY
        next_exetime = retry_delay.get(retried, retry_delay.get('', self.DEFAULT_RETRY_DELAY['']))

        if task['schedule'].get('auto_recrawl') and 'age' in task['schedule']:
            next_exetime = min(next_exetime, task['schedule'].get('age'))
        else:
            if retried >= retries:
                next_exetime = -1
            elif 'age' in task['schedule'] and next_exetime > task['schedule'].get('age'):
                next_exetime = task['schedule'].get('age')

        if next_exetime < 0:
            task['status'] = self.taskdb.FAILED
            task['lastcrawltime'] = time.time()
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
            task['lastcrawltime'] = time.time()
            self.update_task(task)
            self.put_task(task)

            project = task['project']
            self._cnt['5m'].event((project, 'retry'), +1)
            self._cnt['1h'].event((project, 'retry'), +1)
            self._cnt['1d'].event((project, 'retry'), +1)
            # self._cnt['all'].event((project, 'retry'), +1)
            logger.info('task retry %d/%d %%(project)s:%%(taskid)s %%(url)s' % (
                retried, retries), task)
            return task

    def on_select_task(self, task):
        '''Called when a task is selected to fetch & process'''
        # inject informations about project
        logger.info('select %(project)s:%(taskid)s %(url)s', task)

        project_info = self.projects.get(task['project'])
        assert project_info, 'no such project'
        task['group'] = project_info.get('group')
        task['project_md5sum'] = project_info.get('md5sum')
        task['project_updatetime'] = project_info.get('updatetime', 0)
        project_info['active_tasks'].appendleft((time.time(), task))
        self.send_task(task)
        return task


from tornado import gen


class OneScheduler(Scheduler):
    """
    Scheduler Mixin class for one mode

    overwirted send_task method
    call processor.on_task(fetcher.fetch(task)) instead of consuming queue
    """

    def _check_select(self):
        """
        interactive mode of select tasks
        """
        if not self.interactive:
            return super(OneScheduler, self)._check_select()

        # waiting for running tasks
        if self.running_task > 0:
            return

        is_crawled = []

        def run(project=None):
            return crawl('on_start', project=project)

        def crawl(url, project=None, **kwargs):
            """
            Crawl given url, same parameters as BaseHandler.crawl

            url - url or taskid, parameters will be used if in taskdb
            project - can be ignored if only one project exists.
            """

            # looking up the project instance
            if project is None:
                if len(self.projects) == 1:
                    project = list(self.projects.keys())[0]
                else:
                    raise LookupError('You need specify the project: %r'
                                      % list(self.projects.keys()))
            project_data = self.processor.project_manager.get(project)
            if not project_data:
                raise LookupError('no such project: %s' % project)

            # get task package
            instance = project_data['instance']
            instance._reset()
            task = instance.crawl(url, **kwargs)
            if isinstance(task, list):
                raise Exception('url list is not allowed in interactive mode')

            # check task in taskdb
            if not kwargs:
                dbtask = self.taskdb.get_task(task['project'], task['taskid'],
                                              fields=self.request_task_fields)
                if not dbtask:
                    dbtask = self.taskdb.get_task(task['project'], task['url'],
                                                  fields=self.request_task_fields)
                if dbtask:
                    task = dbtask

            # select the task
            self.on_select_task(task)
            is_crawled.append(True)

            shell.ask_exit()

        def quit_interactive():
            '''Quit interactive mode'''
            is_crawled.append(True)
            self.interactive = False
            shell.ask_exit()

        def quit_pyspider():
            '''Close pyspider'''
            is_crawled[:] = []
            shell.ask_exit()

        shell = utils.get_python_console()
        shell.interact(
            'pyspider shell - Select task\n'
            'crawl(url, project=None, **kwargs) - same parameters as BaseHandler.crawl\n'
            'quit_interactive() - Quit interactive mode\n'
            'quit_pyspider() - Close pyspider'
        )
        if not is_crawled:
            self.ioloop.stop()

    def __getattr__(self, name):
        """patch for crawl(url, callback=self.index_page) API"""
        if self.interactive:
            return name
        raise AttributeError(name)

    def on_task_status(self, task):
        """Ignore not processing error in interactive mode"""
        if not self.interactive:
            super(OneScheduler, self).on_task_status(task)

        try:
            procesok = task['track']['process']['ok']
        except KeyError as e:
            logger.error("Bad status pack: %s", e)
            return None

        if procesok:
            ret = self.on_task_done(task)
        else:
            ret = self.on_task_failed(task)
        if task['track']['fetch'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'fetch_time'),
                                       task['track']['fetch']['time'])
        if task['track']['process'].get('time'):
            self._cnt['5m_time'].event((task['project'], 'process_time'),
                                       task['track']['process'].get('time'))
        self.projects[task['project']]['active_tasks'].appendleft((time.time(), task))
        return ret

    def init_one(self, ioloop, fetcher, processor,
                 result_worker=None, interactive=False):
        self.ioloop = ioloop
        self.fetcher = fetcher
        self.processor = processor
        self.result_worker = result_worker
        self.interactive = interactive
        self.running_task = 0

    @gen.coroutine
    def do_task(self, task):
        self.running_task += 1
        result = yield gen.Task(self.fetcher.fetch, task)
        type, task, response = result.args
        self.processor.on_task(task, response)
        # do with message
        while not self.processor.inqueue.empty():
            _task, _response = self.processor.inqueue.get()
            self.processor.on_task(_task, _response)
        # do with results
        while not self.processor.result_queue.empty():
            _task, _result = self.processor.result_queue.get()
            if self.result_worker:
                self.result_worker.on_result(_task, _result)
        self.running_task -= 1

    def send_task(self, task, force=True):
        if self.fetcher.http_client.free_size() <= 0:
            if force:
                self._send_buffer.appendleft(task)
            else:
                raise self.outqueue.Full
        self.ioloop.add_future(self.do_task(task), lambda x: x.result())

    def run(self):
        import tornado.ioloop
        tornado.ioloop.PeriodicCallback(self.run_once, 100,
                                        io_loop=self.ioloop).start()
        self.ioloop.start()

    def quit(self):
        self.ioloop.stop()
        logger.info("scheduler exiting...")


import random
import threading


class ThreadBaseScheduler(Scheduler):
    def __init__(self, threads=4, *args, **kwargs):
        self.threads = threads
        self.local = threading.local()

        super(ThreadBaseScheduler, self).__init__(*args, **kwargs)

        self._taskdb = self.taskdb
        self._projectdb = self.projectdb
        self._resultdb = self.resultdb

        self.thread_objs = []
        self.thread_queues = []
        self._start_threads()
        assert len(self.thread_queues) > 0

    @property
    def taskdb(self):
        if not hasattr(self.local, 'taskdb'):
            self.taskdb = self._taskdb.copy()
        return self.local.taskdb

    @taskdb.setter
    def taskdb(self, taskdb):
        self.local.taskdb = taskdb

    @property
    def projectdb(self):
        if not hasattr(self.local, 'projectdb'):
            self.projectdb = self._projectdb.copy()
        return self.local.projectdb

    @projectdb.setter
    def projectdb(self, projectdb):
        self.local.projectdb = projectdb

    @property
    def resultdb(self):
        if not hasattr(self.local, 'resultdb'):
            self.resultdb = self._resultdb.copy()
        return self.local.resultdb

    @resultdb.setter
    def resultdb(self, resultdb):
        self.local.resultdb = resultdb

    def _start_threads(self):
        for i in range(self.threads):
            queue = Queue.Queue()
            thread = threading.Thread(target=self._thread_worker, args=(queue, ))
            thread.daemon = True
            thread.start()
            self.thread_objs.append(thread)
            self.thread_queues.append(queue)

    def _thread_worker(self, queue):
        while True:
            method, args, kwargs = queue.get()
            try:
                method(*args, **kwargs)
            except Exception as e:
                logger.exception(e)

    def _run_in_thread(self, method, *args, **kwargs):
        i = kwargs.pop('_i', None)
        block = kwargs.pop('_block', False)

        if i is None:
            while True:
                for queue in self.thread_queues:
                    if queue.empty():
                        break
                else:
                    if block:
                        time.sleep(0.1)
                        continue
                    else:
                        queue = self.thread_queues[random.randint(0, len(self.thread_queues)-1)]
                break
        else:
            queue = self.thread_queues[i % len(self.thread_queues)]

        queue.put((method, args, kwargs))

        if block:
            self._wait_thread()

    def _wait_thread(self):
        while True:
            if all(queue.empty() for queue in self.thread_queues):
                break
            time.sleep(0.1)

    def _update_project(self, project):
        self._run_in_thread(Scheduler._update_project, self, project)

    def on_task_status(self, task):
        i = hash(task['taskid'])
        self._run_in_thread(Scheduler.on_task_status, self, task, _i=i)

    def on_request(self, task):
        i = hash(task['taskid'])
        self._run_in_thread(Scheduler.on_request, self, task, _i=i)

    def _load_put_task(self, project, taskid):
        i = hash(taskid)
        self._run_in_thread(Scheduler._load_put_task, self, project, taskid, _i=i)

    def run_once(self):
        super(ThreadBaseScheduler, self).run_once()
        self._wait_thread()
