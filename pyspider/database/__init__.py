#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-08 15:04:08

import urlparse


def connect_database(url):
    """
    create database object by url

    mysql:
        mysql+type://user:passwd@host:port/database
    sqlite:
        # relative path
        sqlite+type:///path/to/database.db
        # absolute path
        sqlite+type:////path/to/database.db
        # memory database
        sqlite+type://
    mongodb:
        mongodb+type://[username:password@]host1[:port1][,host2[:port2],...[,hostN[:portN]]][/[database][?options]]

    type:
        taskdb
        projectdb
        resultdb

    """
    parsed = urlparse.urlparse(url)
    engine, dbtype = parsed.scheme.split('+')
    if engine == 'mysql':
        parames = {}
        if parsed.username:
            parames['user'] = parsed.username
        if parsed.password:
            parames['passwd'] = parsed.password
        if parsed.hostname:
            parames['host'] = parsed.hostname
        if parsed.port:
            parames['port'] = parsed.port
        if parsed.path.strip('/'):
            parames['database'] = parsed.path.strip('/')

        if dbtype == 'taskdb':
            from .mysql.taskdb import TaskDB
            return TaskDB(**parames)
        elif dbtype == 'projectdb':
            from .mysql.projectdb import ProjectDB
            return ProjectDB(**parames)
        elif dbtype == 'resultdb':
            from .mysql.resultdb import ResultDB
            return ResultDB(**parames)
        else:
            raise Exception('unknow database type: %s' % dbtype)
    elif engine == 'sqlite':
        if parsed.path.startswith('//'):
            path = '/' + parsed.path.strip('/')
        elif parsed.path.startswith('/'):
            path = './' + parsed.path.strip('/')
        elif not parsed.path:
            path = ':memory:'
        else:
            raise Exception('error path: %s' % parsed.path)

        if dbtype == 'taskdb':
            from .sqlite.taskdb import TaskDB
            return TaskDB(path)
        elif dbtype == 'projectdb':
            from .sqlite.projectdb import ProjectDB
            return ProjectDB(path)
        elif dbtype == 'resultdb':
            from .sqlite.resultdb import ResultDB
            return ResultDB(path)
        else:
            raise Exception('unknow database type: %s' % dbtype)
    elif engine == 'mongodb':
        url = url.replace(parsed.scheme, 'mongodb')
        parames = {}
        if parsed.path.strip('/'):
            parames['database'] = parsed.path.strip('/')

        if dbtype == 'taskdb':
            from .mongodb.taskdb import TaskDB
            return TaskDB(url, **parames)
        elif dbtype == 'projectdb':
            from .mongodb.projectdb import ProjectDB
            return ProjectDB(url, **parames)
        elif dbtype == 'resultdb':
            from .mongodb.resultdb import ResultDB
            return ResultDB(url, **parames)
        else:
            raise Exception('unknow database type: %s' % dbtype)
    else:
        raise Exception('unknow engine: %s' % engine)
