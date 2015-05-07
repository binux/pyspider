#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:20:39

import socket
import inspect
import datetime

from pyspider.libs import sample_handler

from flask import render_template, request, json
from flask.ext import login
from .app import app
import re

index_fields = ['name', 'group', 'status', 'comments', 'rate', 'burst', 'updatetime']
default_script = inspect.getsource(sample_handler)

@app.route('/')
def index():
    projectdb = app.config['projectdb']

    return render_template("index.html", projects=projectdb.get_all(fields=index_fields))

@app.route('/create', methods=['POST', ]) 
def project_save():
    project = request.form['name']
    target_site = request.form['target'] # Won't do anything with this data just yet
    group = request.form['group']

    if re.search(r"[^\w]", project):
        print("\n--In here--\n")
        return 'project name is not allowed!', 400

    projectdb = app.config['projectdb']
    info = {
            'name': project,
            'status': 'TODO',
            'rate': app.config.get('max_rate', 1),
            'burst': app.config.get('max_burst', 3),
            'group': group,
            'script': (default_script
                  .replace('__DATE__', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
                  .replace('__PROJECT_NAME__', project)),

        }
    projectdb.insert(project, info)

    rpc = app.config['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            app.logger.warning('connect to scheduler rpc error: %r', e)
            return 'rpc error', 200

    return 'ok', 200



@app.route('/queues')
def get_queues():
    def try_get_qsize(queue):
        if queue is None:
            return 'None'
        try:
            return queue.qsize()
        except NotImplementedError:
            return 'Not Available For OSX'
        except Exception as e:
            return "%r" % e

    result = {}
    queues = app.config.get('queues', {})
    for key in queues:
        result[key] = try_get_qsize(queues[key])
    return json.dumps(result), 200, {'Content-Type': 'application/json'}


@app.route('/update', methods=['POST', ])
def project_update():
    projectdb = app.config['projectdb']
    project = request.form['pk']
    name = request.form['name']
    value = request.form['value']

    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return "no such project.", 404
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    if name not in ('group', 'status', 'rate'):
        return 'unknown field: %s' % name, 400
    if name == 'rate':
        value = value.split('/')
        if len(value) != 2:
            return 'format error: rate/burst', 400
        rate = float(value[0])
        burst = float(value[1])
        update = {
            'rate': min(rate, app.config.get('max_rate', rate)),
            'burst': min(burst, app.config.get('max_burst', burst)),
        }
    else:
        update = {
            name: value
        }

    ret = projectdb.update(project, update)
    if ret:
        rpc = app.config['scheduler_rpc']
        if rpc is not None:
            try:
                rpc.update_project()
            except socket.error as e:
                app.logger.warning('connect to scheduler rpc error: %r', e)
                return 'rpc error', 200
        return 'ok', 200
    else:
        return 'update error', 500


@app.route('/counter')
def counter():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    result = {}
    try:
        for project, counter in rpc.counter('5m_time', 'avg').items():
            result.setdefault(project, {})['5m_time'] = counter
        for project, counter in rpc.counter('5m', 'sum').items():
            result.setdefault(project, {})['5m'] = counter
        for project, counter in rpc.counter('1h', 'sum').items():
            result.setdefault(project, {})['1h'] = counter
        for project, counter in rpc.counter('1d', 'sum').items():
            result.setdefault(project, {})['1d'] = counter
        for project, counter in rpc.counter('all', 'sum').items():
            result.setdefault(project, {})['all'] = counter
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({}), 200, {'Content-Type': 'application/json'}

    return json.dumps(result), 200, {'Content-Type': 'application/json'}


@app.route('/run', methods=['POST', ])
def runtask():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    projectdb = app.config['projectdb']
    project = request.form['project']
    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return "no such project.", 404
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return app.login_response

    newtask = {
        "project": project,
        "taskid": "on_start",
        "url": "data:,on_start",
        "process": {
            "callback": "on_start",
        },
        "schedule": {
            "age": 0,
            "priority": 9,
            "force_update": True,
        },
    }

    try:
        ret = rpc.newtask(newtask)
    except socket.error as e:
        app.logger.warning('connect to scheduler rpc error: %r', e)
        return json.dumps({"result": False}), 200, {'Content-Type': 'application/json'}
    return json.dumps({"result": ret}), 200, {'Content-Type': 'application/json'}


@app.route('/robots.txt')
def robots():
    return """User-agent: *
Disallow: /
Allow: /$
Allow: /debug
Disallow: /debug/*?taskid=*
""", 200, {'Content-Type': 'text/plain'}
