#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-08 10:28:48

# task schema
{
'task': {
        'taskid': str, # new, not change
        'project': str, # new, not change
        'url': str, # new, not change
        'status': int, # change
        'schedule': {
            'priority': int,
            'retries': int,
            'exetime': int,
            'age': int,
            'itag': str, #
            #'recrawl': int
            }, # new and restart
        'fetch': {
            'method': str,
            'headers': dict, 
            'data': str, 
            'timeout': int,
            }, # new and restart 
        'process': {
            'callback': str,
            'save': dict,
            }, # new and restart
        'track': {
            'fetch': {
                'ok': bool,
                'time': int,
                'status_code': int,
                'headers': dict, 
                'encoding': str,
                'content': str,
                },
            'process': {
                'ok': bool,
                'time': int,
                'follows': int,
                'outputs': int,
                #'exception': "?",
                },
            }, # finish
        'lastcrawltime': int, # keep between request
        'updatetime': int, # keep between request
        }
}


class TaskDB(object):
    ACTIVE = 1
    SUCCESS = 2
    FAILED = 3
    BAD = 4

    def load_tasks(self, status, project=None, fields=None):
        raise NotImplementedError

    def get_task(self, project, taskid, fields=None):
        raise NotImplementedError

    def status_count(self, project):
        '''
        return a dict
        '''
        raise NotImplementedError

    def insert(self, project, taskid, obj={}):
        raise NotImplementedError
        
    def update(self, project, taskid, obj={}, **kwargs):
        raise NotImplementedError
