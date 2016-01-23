#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-08 15:04:08

from six.moves.urllib.parse import urlparse, parse_qs


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
        more: http://docs.mongodb.org/manual/reference/connection-string/
    sqlalchemy:
        sqlalchemy+postgresql+type://user:passwd@host:port/database
        sqlalchemy+mysql+mysqlconnector+type://user:passwd@host:port/database
        more: http://docs.sqlalchemy.org/en/rel_0_9/core/engines.html
    redis:
        redis+taskdb://host:port/db
    elasticsearch:
        elasticsearch+type://host:port/?index=pyspider
    local:
        local+projectdb://filepath,filepath

    type:
        taskdb
        projectdb
        resultdb

    """
    db = _connect_database(url)
    db.copy = lambda: _connect_database(url)
    return db


def _connect_database(url):  # NOQA
    parsed = urlparse(url)

    scheme = parsed.scheme.split('+')
    if len(scheme) == 1:
        raise Exception('wrong scheme format: %s' % parsed.scheme)
    else:
        engine, dbtype = scheme[0], scheme[-1]
        other_scheme = "+".join(scheme[1:-1])

    if dbtype not in ('taskdb', 'projectdb', 'resultdb'):
        raise LookupError('unknown database type: %s, '
                          'type should be one of ["taskdb", "projectdb", "resultdb"]', dbtype)

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
            raise LookupError
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
            raise LookupError
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
            raise LookupError
    elif engine == 'sqlalchemy':
        if not other_scheme:
            raise Exception('wrong scheme format: %s' % parsed.scheme)
        url = url.replace(parsed.scheme, other_scheme)

        if dbtype == 'taskdb':
            from .sqlalchemy.taskdb import TaskDB
            return TaskDB(url)
        elif dbtype == 'projectdb':
            from .sqlalchemy.projectdb import ProjectDB
            return ProjectDB(url)
        elif dbtype == 'resultdb':
            from .sqlalchemy.resultdb import ResultDB
            return ResultDB(url)
        else:
            raise LookupError
    elif engine == 'redis':
        if dbtype == 'taskdb':
            from .redis.taskdb import TaskDB
            return TaskDB(parsed.hostname, parsed.port,
                          int(parsed.path.strip('/') or 0))
        else:
            raise LookupError('not supported dbtype: %s', dbtype)
    elif engine == 'local':
        scripts = url.split('//', 1)[1].split(',')
        if dbtype == 'projectdb':
            from .local.projectdb import ProjectDB
            return ProjectDB(scripts)
        else:
            raise LookupError('not supported dbtype: %s', dbtype)
    elif engine == 'elasticsearch' or engine == 'es':
        index = parse_qs(parsed.query)
        if 'index' in index and index['index']:
            index = index['index'][0]
        else:
            index = 'pyspider'

        if dbtype == 'projectdb':
            from .elasticsearch.projectdb import ProjectDB
            return ProjectDB([parsed.netloc], index=index)
        elif dbtype == 'resultdb':
            from .elasticsearch.resultdb import ResultDB
            return ResultDB([parsed.netloc], index=index)
        elif dbtype == 'taskdb':
            from .elasticsearch.taskdb import TaskDB
            return TaskDB([parsed.netloc], index=index)
    else:
        raise Exception('unknown engine: %s' % engine)
