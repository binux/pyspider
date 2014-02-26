#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-23 00:19:06


import sys
import datetime
from app import app
from flask import abort, render_template, request, json

default_task = {
        'taskid': 'data:,on_start',
        'project': '',
        'url': 'data:,on_start',
        'process': {
            'callback': 'on_start',
            },
        }
default_script = open('libs/sample_handler.py').read()

@app.route('/debug/<project>')
def debug(project):
    default_task['project'] = project
    script = default_script.replace('__DATE__', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return render_template("debug.html", task=default_task, script=script)


import time
import traceback
from libs.utils import hide_me
from libs.response import rebuild_response
from processor.processor import build_module

@app.route('/debug/<project>/run', methods=['POST', ])
def run(project):
    task = json.loads(request.form['task'])
    project_info = {
            'name': project,
            'status': 'DEBUG',
            'script': request.form['script'],
            }

    try:
        task, fetch_result = app.config['fetch'](task)
        response = rebuild_response(fetch_result)
        start_time = time.time()
        module = build_module(project_info, {'debugger': True})
        ret = module['instance'].run(module['module'], task, response)
    except Exception, e:
        type, value, tb = sys.exc_info()
        tb = hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        result = {
                'fetch_result': fetch_result,
                'logs': logs,
                'follows': [],
                'messages': [],
                'result': None,
                'time': time.time() - start_time,
                }
    else:
        result = {
                'fetch_result': fetch_result,
                'logs': ret.logstr(),
                'follows': ret.follows,
                'messages': ret.messages,
                'result': ret.result,
                'time': time.time() - start_time,
                }
        result['fetch_result']['content'] = response.text

    return json.dumps(result), 200, {'Content-Type': 'application/json'}
