#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:20:39

from app import app
from flask import abort, render_template, request, json


index_fields = ['name', 'group', 'status', 'comments', 'rate', 'burst', ]
@app.route('/')
def index():
    projectdb = app.config['projectdb']
    return render_template("index.html", projects=projectdb.get_all(fields=index_fields))

@app.route('/update', methods=['POST', ])
def project_update():
    projectdb = app.config['projectdb']
    project = request.form['pk']
    name = request.form['name']
    value = request.form['value']

    if name not in ('group', 'status', 'rate'):
        return 'unknow field: %s' % name, 400
    if name == 'rate':
        value = value.split('/')
        if len(value) != 2:
            return 'format error: rate/burst', 400
        update = {
                'rate': float(value[0]),
                'burst': float(value[1]),
                }
    else:
        update = {
                name: value
                }
    
    ret = projectdb.update(project, update)
    if ret:
        rpc = app.config['scheduler_rpc']
        rpc.update_project()
        return 'ok', 200
    else:
        return 'update error', 500

@app.route('/counter')
def counter():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    time = request.args['time']
    type = request.args.get('type', 'sum')

    return json.dumps(rpc.counter(time, type)), 200, {'Content-Type': 'application/json'}

@app.route('/run', methods=['POST', ])
def runtask():
    rpc = app.config['scheduler_rpc']
    if rpc is None:
        return json.dumps({})

    project = request.form['project']
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

    ret = rpc.newtask(newtask)
    return json.dumps({"result": ret}), 200, {'Content-Type': 'application/json'}
