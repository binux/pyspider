#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:17:13

import __builtin__
import os
import sys
import urlparse
from flask import Flask, Response
from pyspider.fetcher import tornado_fetcher

if os.name == 'nt':
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)

app = Flask('webui',
            static_folder=os.path.join(os.path.dirname(__file__), 'static'),
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.urandom(24)
app.jinja_env.line_statement_prefix = '#'
app.jinja_env.globals.update(__builtin__.__dict__)

app.config.update({
    'fetch': lambda x: tornado_fetcher.Fetcher(None, None, async=False).fetch(x)[1],
    'taskdb': None,
    'projectdb': None,
    'scheduler_rpc': None,
})

import base64
from flask.ext import login
login_manager = login.LoginManager()
login_manager.init_app(app)


class User(login.UserMixin):

    def __init__(self, id, password):
        self.id = id
        self.password = password

    def is_authenticated(self):
        if not app.config.get('webui_username'):
            return True
        if self.id == app.config.get('webui_username') \
                and self.password == app.config.get('webui_password'):
            return True
        return False

    def is_active(self):
        return self.is_authenticated()


@login_manager.request_loader
def load_user_from_request(request):
    api_key = request.headers.get('Authorization')
    if api_key:
        api_key = api_key.replace('Basic ', '', 1)
        try:
            api_key = base64.b64decode(api_key)
        except TypeError:
            pass
        return User(*api_key.split(":", 1))
    return None
app.login_response = Response(
    "need auth.", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}
)


def cdn_url_handler(error, endpoint, kwargs):
    if endpoint == 'cdn':
        path = kwargs.pop('path')
        # cdn = app.config.get('cdn', 'http://cdn.staticfile.org/')
        # cdn = app.config.get('cdn', '//cdnjs.cloudflare.com/ajax/libs/')
        cdn = app.config.get('cdn', '//cdnjscn.b0.upaiyun.com/libs/')
        return urlparse.urljoin(cdn, path)
    else:
        exc_type, exc_value, tb = sys.exc_info()
        if exc_value is error:
            raise exc_type, exc_value, tb
        else:
            raise error
app.handle_url_build_error = cdn_url_handler
