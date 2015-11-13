#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-09-30 23:22:46

import click
import logging
from pyspider.database.base.projectdb import ProjectDB
from pyspider.database.base.taskdb import TaskDB
from pyspider.database.base.resultdb import ResultDB
from pyspider.database import connect_database
from pyspider.libs.utils import unicode_obj
from multiprocessing.pool import ThreadPool as Pool

logging.getLogger().setLevel(logging.INFO)


def taskdb_migrating(project, from_connection, to_connection):
    logging.info("taskdb: %s", project)
    f = connect_database(from_connection)
    t = connect_database(to_connection)
    t.drop(project)
    for status in range(1, 5):
        for task in f.load_tasks(status, project=project):
            t.insert(project, task['taskid'], task)


def resultdb_migrating(project, from_connection, to_connection):
    logging.info("resultdb: %s", project)
    f = connect_database(from_connection)
    t = connect_database(to_connection)
    t.drop(project)
    for result in f.select(project):
        t.save(project, result['taskid'], result['url'], result['result'])


@click.command()
@click.option('--pool', default=10, help='cocurrent worker size.')
@click.argument('from_connection', required=1)
@click.argument('to_connection', required=1)
def migrate(pool, from_connection, to_connection):
    """
    Migrate tool for pyspider
    """
    f = connect_database(from_connection)
    t = connect_database(to_connection)

    if isinstance(f, ProjectDB):
        for each in f.get_all():
            each = unicode_obj(each)
            logging.info("projectdb: %s", each['name'])
            t.drop(each['name'])
            t.insert(each['name'], each)
    elif isinstance(f, TaskDB):
        pool = Pool(pool)
        pool.map(
            lambda x, f=from_connection, t=to_connection: taskdb_migrating(x, f, t),
            f.projects)
    elif isinstance(f, ResultDB):
        pool = Pool(pool)
        pool.map(
            lambda x, f=from_connection, t=to_connection: resultdb_migrating(x, f, t),
            f.projects)


if __name__ == '__main__':
    migrate()
