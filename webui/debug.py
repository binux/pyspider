#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-23 00:19:06


import re
import sys
import time
import datetime
import traceback
from app import app
from flask import abort, render_template, request, json
from libs.utils import hide_me, timeout
from libs.response import rebuild_response
from processor.processor import build_module
from processor.project_module import ProjectFinder, ProjectLoader

default_task = {
        'taskid': 'data:,on_start',
        'project': '',
        'url': 'data:,on_start',
        'process': {
            'callback': 'on_start',
            },
        }
default_script = open('libs/sample_handler.py').read()

def verify_project_name(project):
    if re.search(r"[^\w]", project):
        return False
    return True

@app.route('/debug/<project>')
def debug(project):
    if not verify_project_name(project):
        return 'project name is not allowed!', 400
    projectdb = app.config['projectdb']
    info = projectdb.get(project)
    if info:
        script = info['script']
    else:
        script = default_script.replace('__DATE__', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    taskid = request.args.get('taskid')
    if taskid:
        taskdb = app.config['taskdb']
        task = taskdb.get_task(project, taskid, ['taskid', 'project', 'url', 'process'])
    else:
        task = default_task

    default_task['project'] = project
    return render_template("debug.html", task=task, script=script, project_name=project)

@app.before_first_request
def enable_projects_import():
    class DebuggerProjectFinder(ProjectFinder):
        def get_loader(self, name):
            info = app.config['projectdb'].get(name)
            if info:
                return ProjectLoader(info)
    sys.meta_path.append(DebuggerProjectFinder())

@app.route('/debug/<project>/run', methods=['POST', ])
def run(project):
    task = json.loads(request.form['task'])
    project_info = {
            'name': project,
            'status': 'DEBUG',
            'script': request.form['script'],
            }

    fetch_result = {}
    start_time = time.time()
    try:
        with timeout(30):
            fetch_result = app.config['fetch'](task)
            response = rebuild_response(fetch_result)
            module = build_module(project_info, {
                'debugger': True
                })
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

    try:
        return json.dumps(result), 200, {'Content-Type': 'application/json'}
    except Exception, e:
        type, value, tb = sys.exc_info()
        tb = hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        result = {
                'fetch_result': "",
                'logs': logs,
                'follows': [],
                'messages': [],
                'result': None,
                'time': time.time() - start_time,
                }
        return json.dumps(result), 200, {'Content-Type': 'application/json'}

@app.route('/debug/<project>/save', methods=['POST', ])
def save(project):
    if not verify_project_name(project):
        return 'project name is not allowed!', 400
    projectdb = app.config['projectdb']
    script = request.form['script']
    old_project = projectdb.get(project, fields=['name', 'status', ])
    if old_project:
        info = {
            'script': script,
            }
        if old_project.get('status') in ('DEBUG', 'RUNNING', ):
            info['status'] = 'CHECKING'
        projectdb.update(project, info)
    else:
        info = {
            'name': project,
            'script': script,
            'status': 'TODO',
            'rate': 1,
            'burst': 10
            }
        projectdb.insert(project, info)

    rpc = app.config['scheduler_rpc']
    rpc.update_project()

    return 'OK', 200

@app.route('/helper.js')
def resizer_js():
    host = request.headers['Host']
    return render_template("helper.js", host=host), 200, {'Content-Type': 'application/javascript'}

@app.route('/helper.html')
def resizer_html():
    height = request.args.get('height')
    script = request.args.get('script', '')
    return render_template("helper.html", height=height, script=script)
