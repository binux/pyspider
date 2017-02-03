#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-23 00:19:06


import sys
import time
import socket

import traceback
from flask import render_template, request, json, current_app, jsonify
from flask import Blueprint
from werkzeug.exceptions import HTTPException

from pyspider.libs import utils, dataurl
from pyspider.libs.response import rebuild_response
from pyspider.processor.project_module import ProjectManager, ProjectFinder
from pyspider.libs.samples import get_sample_handler, get_sample_task
from pyspider.webui._compat import login


bp = Blueprint("debug", __name__, url_prefix='/debug')


class Result(object):
    def __init__(self, fetch_result='', logs=u'', follows=None, messages=None, result=None):
        if follows is None:
            follows = []
        if messages is None:
            messages = []
        self.fetch_result = fetch_result
        self.logs= logs
        self.follows = follows
        self.messages = messages
        self.result = result
        self.time = 0

    def render(self, start_time=None):
        if start_time is not None:
            self.time = time.time() - start_time
        data = {
            'fetch_result': self.fetch_result,
            'logs': self.logs,
            'follows': self.follows,
            'messages': self.messages,
            'result': self.result,
            'time': self.time
        }
        return utils.unicode_dict(data)


def check_project(projectdb, project):
    if not projectdb.verify_project_name(project):
        raise HTTPException("project name is not allowed!", 400)


@bp.route('/<project>', methods=['GET', 'POST'])
def debug(project):
    config = current_app.config
    projectdb = config['projectdb']
    check_project(projectdb, project)

    info = projectdb.get(project, fields=['name', 'script'])
    if info:
        script = info['script']
    else:
        script = get_sample_handler(project, request.values.get('start-urls'))

    taskid = request.args.get('taskid')
    if taskid:
        taskdb = config['taskdb']
        task = taskdb.get_task(
            project, taskid, ['taskid', 'project', 'url', 'fetch', 'process'])
    else:
        task = get_sample_task()

    return render_template("debug.html", task=task, script=script, project_name=project)


@bp.route('/<project>/run', methods=['POST', ])
def run(project):
    config = current_app.config
    start_time = time.time()
    try:
        task = utils.decode_unicode_obj(json.loads(request.form['task']))
    except Exception:
        res = Result(logs=u'task json error')
        return jsonify(res.render(start_time))

    project_info = {
        'name': project,
        'status': 'DEBUG',
        'script': request.form['script'],
    }

    if request.form.get('webdav_mode') == 'true':
        projectdb = config['projectdb']
        info = projectdb.get(project, fields=['name', 'script'])
        if not info:
            res = Result(logs=u'  in wevdav mode, cannot load script')
            return jsonify(res.render(start_time))
        project_info['script'] = info['script']

    fetch_result = {}
    try:
        module = ProjectManager.build_module(project_info, {
            'debugger': True,
            'process_time_limit': config['process_time_limit'],
        })

        # The code below is to mock the behavior that crawl_config been joined when selected by scheduler.
        # but to have a better view of joined tasks, it has been done in BaseHandler.crawl when `is_debugger is True`
        # crawl_config = module['instance'].crawl_config
        # task = module['instance'].task_join_crawl_config(task, crawl_config)

        fetch_result = config['fetch'](task)
        response = rebuild_response(fetch_result)

        ret = module['instance'].run_task(module['module'], task, response)
    except Exception:
        type, value, tb = sys.exc_info()
        tb = utils.hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        res = Result(fetch_result=fetch_result, logs=logs)
    else:
        fetch_result['content'] = response.text
        if response.headers.get('content-type', '').startswith('image'):
            fetch_result['dataurl'] = dataurl.encode(
                response.content, response.headers['content-type'])
        res = Result(fetch_result=fetch_result, logs=ret.logstr,
                     follows=ret.follows, messages=ret.messages, result=ret.result)

    try:
        # binary data can't encode to JSON, encode result as unicode obj
        # before send it to frontend
        return jsonify(res.render(start_time))
    except Exception:
        type, value, tb = sys.exc_info()
        tb = utils.hide_me(tb, globals())
        logs = ''.join(traceback.format_exception(type, value, tb))
        res = Result(logs=logs)
        return jsonify(res.render(start_time))


@bp.route('/<project>/save', methods=['POST', ])
def save(project):
    config = current_app.config
    projectdb = config['projectdb']
    check_project(projectdb, project)

    script = request.form['script']
    project_info = projectdb.get(project, fields=['name', 'status', 'group'])
    if project_info and 'lock' in projectdb.split_group(project_info.get('group')) \
            and not login.current_user.is_active():
        return config['login_response']

    if project_info:
        info = {
            'script': script,
        }
        if project_info.get('status') in ('DEBUG', 'RUNNING', ):
            info['status'] = 'CHECKING'
        projectdb.update(project, info)
    else:
        info = {
            'name': project,
            'script': script,
            'status': 'TODO',
            'rate': config.get('max_rate', 1),
            'burst': config.get('max_burst', 3),
        }
        projectdb.insert(project, info)

    rpc = config['scheduler_rpc']
    if rpc is not None:
        try:
            rpc.update_project()
        except socket.error as e:
            current_app.logger.warning('connect to scheduler rpc error: %r', e)
            return 'rpc error'
    return 'ok'


@bp.route('/<project>/get')
def get_script(project):
    projectdb = current_app.config['projectdb']
    check_project(projectdb, project)

    info = projectdb.get(project, fields=['name', 'script'])
    return jsonify(utils.unicode_obj(info))


@bp.route('/blank.html')
def blank_html():
    return ""
