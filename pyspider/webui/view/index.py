#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:20:39

import socket
from flask import Blueprint
from flask import render_template, request, json, current_app, jsonify
from pandas.compat import iteritems
from werkzeug.exceptions import HTTPException

from pyspider.webui._compat import login


bp = Blueprint('index', __name__)


index_fields = ['name', 'group', 'status', 'comments', 'rate', 'burst', 'updatetime']


@bp.route('/')
def index():
    projectdb = current_app.config['projectdb']
    projects = sorted(projectdb.get_all(fields=index_fields),
                      key=lambda k: (0 if k['group'] else 1, k['group'] or '', k['name']))
    return render_template("index.html", projects=projects)


def try_get_qsize(queue):
    if queue is None:
        return 'None'
    try:
        return queue.qsize()
    except Exception as e:
        return "%r" % e


@bp.route('/queues')
def get_queues():
    result = {}
    queues = current_app.config.get('queues', {})
    for key in queues:
        result[key] = try_get_qsize(queues[key])
    return jsonify(result)


@bp.route('/update', methods=['POST', ])
def project_update():
    config = current_app.config
    projectdb = config['projectdb']
    project = request.form['pk']
    name = request.form['name']
    value = request.form['value']

    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        raise HTTPException("no such project.", 404)
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return current_app.login_response

    if name not in ('group', 'status', 'rate'):
        msg = 'unknown field: %s' % name
        raise HTTPException(msg, 400)
    if name == 'rate':
        value = value.split('/')
        if len(value) != 2:
            raise HTTPException('format error: rate/burst', 400)
        rate = float(value[0])
        burst = float(value[1])
        update = {
            'rate': min(rate, config.get('max_rate', rate)),
            'burst': min(burst, config.get('max_burst', burst)),
        }
    else:
        update = {
            name: value
        }

    ret = projectdb.update(project, update)
    if ret:
        rpc = config['scheduler_rpc']
        if rpc is not None:
            try:
                rpc.update_project()
            except socket.error as e:
                current_app.logger.warning('connect to scheduler rpc error: %r', e)
                return 'rpc error'
        return 'ok'
    else:
        raise HTTPException("update error", 500)


@bp.route('/counter')
def counter():
    config = current_app.config
    rpc = config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    result = {}
    try:
        data = rpc.webui_update()
        for type, counters in iteritems(data['counter']):
            for project, counter in iteritems(counters):
                result.setdefault(project, {})[type] = counter
        for project, paused in iteritems(data['pause_status']):
            result.setdefault(project, {})['paused'] = paused
    except socket.error as e:
        current_app.logger.warning('connect to scheduler rpc error: %r', e)
        return jsonify({})
    return jsonify(result)


@bp.route('/run', methods=['POST', ])
def runtask():
    config = current_app.config
    rpc = config['scheduler_rpc']
    if rpc is None:
        return jsonify({})

    projectdb = config['projectdb']
    project = request.form['project']
    project_info = projectdb.get(project, fields=('name', 'group'))
    if not project_info:
        return "no such project.", 404
    if 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return current_app.login_response

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

    ret = False
    try:
        ret = rpc.newtask(newtask)
    except socket.error as e:
        current_app.logger.warning('connect to scheduler rpc error: %r', e)
    return jsonify({"result": ret})


@bp.route('/robots.txt')
def robots():
    return """User-agent: *
Disallow: /
Allow: /$
Allow: /debug
Disallow: /debug/*?taskid=*
""", 200, {'Content-Type': 'text/plain'}
