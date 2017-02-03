#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:20:40

import os
import sys

import logging
from importlib import import_module
from flask import current_app
from flask import Blueprint, Response
from werkzeug.exceptions import Unauthorized

from pyspider.libs import utils
from pyspider.processor.project_module import ProjectFinder
from .app import QuitableFlask
from pyspider.fetcher import tornado_fetcher
from ._compat import builtins, urljoin, reraise

path = os.path

base_dir = path.dirname(__file__)

logger = logging.getLogger("webui")


def full_path(p):
    return path.join(base_dir, p)

if os.name == 'nt':
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)


def _fetch(url):
    return tornado_fetcher.Fetcher(None, None, async=False).fetch(url)


def init_config(app):
    app.config.update({
        'fetch': _fetch,
        'taskdb': None,
        'projectdb': None,
        'scheduler_rpc': None,
        'queues': dict(),
        'process_time_limit': 30,
        'login_response': Response("need auth.", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})
    })


def init_jinja(app):
    app.jinja_env.line_statement_prefix = '#'
    app.jinja_env.globals.update(builtins.__dict__)
    app.template_filter('format_date')(utils.format_date)


def init_session(app):
    app.secret_key = os.urandom(24)


def init_view(app):
    bp_modules = ('debug',  'task', 'index', 'bench_test', 'result')
    for bp_module in bp_modules:
        module = '.view.%s' % bp_module
        module_instance = import_module(module, __name__)
        bp = getattr(module_instance, 'bp')
        if bp and isinstance(bp, Blueprint):
            app.register_blueprint(bp)


def cdn_url_handler(error, endpoint, kwargs):
    if endpoint == 'cdn':
        path = kwargs.pop('path')
        # cdn = app.config.get('cdn', 'http://cdn.staticfile.org/')
        # cdn = app.config.get('cdn', '//cdnjs.cloudflare.com/ajax/libs/')
        cdn = current_app.config.get('cdn', '//cdnjscn.b0.upaiyun.com/libs/')
        return urljoin(cdn, path)
    else:
        exc_type, exc_value, tb = sys.exc_info()
        if exc_value is error:
            reraise(exc_type, exc_value, tb)
        else:
            raise error


def init_url_handler(app):
    app.handle_url_build_error = cdn_url_handler


def init_login(app):
    from .login import login_manager
    login_manager.init_app(app)


    from ._compat import login

    @app.before_request
    def before_request():
        config = current_app.config
        if config.get('need_auth', True):
            if not login.current_user.is_active():
                return config['login_response']


def init_project_import(app):
    sys.meta_path.append(ProjectFinder(app.config['projectdb']))


def init_webdav(app):
    try:
        from .webdav import init_webdav
        init_webdav(app)
    except ImportError as e:
        logger.warning('WebDav interface not enabled: %r', e)


def create_app():
    static_folder = full_path('static')
    template_folder = full_path('templates')
    app = QuitableFlask(__name__,
                        static_folder=static_folder,
                        template_folder=template_folder)
    init_config(app)
    init_jinja(app)
    init_session(app)
    init_view(app)
    init_url_handler(app)
    init_login(app)
    init_project_import(app)
    return app


app = create_app()
