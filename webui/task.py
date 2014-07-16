#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-07-16 15:30:57

from app import app
from flask import abort, render_template, request, json

from libs import utils

@app.route('/task/<taskid>')
def task(taskid):
    if ':' not in taskid:
        abort(400)
    project, taskid = taskid.split(':', 1)

    taskdb = app.config['taskdb']
    task = taskdb.get_task(project, taskid)

    return render_template("task.html", task=task, json=json,
            status_to_string=app.config['taskdb'].status_to_string)

app.template_filter('format_date')(utils.format_date)
