#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:19:11

import xmlrpclib

from webui.app import app
from database.sqlite import taskdb, projectdb

config = {
        'taskdb': taskdb.TaskDB('./data/task.db'),
        'projectdb': projectdb.ProjectDB('data/project.db'),
        'scheduler_rpc': xmlrpclib.ServerProxy('http://localhost:23333', allow_none=True),
        }

if __name__ == '__main__':
    app.config.update(**config)
    app.debug = True
    app.run()
