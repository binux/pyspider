#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:17:13

import os
import sys
import logging
logger = logging.getLogger("webui")

from six import reraise
from six.moves import builtins
from six.moves.urllib.parse import urljoin
from flask import Flask
from pyspider.fetcher import tornado_fetcher

if os.name == 'nt':
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)


class QuitableFlask(Flask):
    """Add quit() method to Flask object"""

    @property
    def logger(self):
        return logger

    def run(self, host=None, port=None, debug=None, **options):
        import tornado.wsgi
        import tornado.ioloop
        import tornado.httpserver
        import tornado.web

        if host is None:
            host = '127.0.0.1'
        if port is None:
            server_name = self.config['SERVER_NAME']
            if server_name and ':' in server_name:
                port = int(server_name.rsplit(':', 1)[1])
            else:
                port = 5000
        if debug is not None:
            self.debug = bool(debug)

        hostname = host
        port = port
        application = self
        use_reloader = self.debug
        use_debugger = self.debug

        if use_debugger:
            from werkzeug.debug import DebuggedApplication
            application = DebuggedApplication(application, True)

        try:
            from .webdav import dav_app
        except ImportError as e:
            logger.warning('WebDav interface not enabled: %r', e)
            dav_app = None
        if dav_app:
            from werkzeug.wsgi import DispatcherMiddleware
            application = DispatcherMiddleware(application, {
                '/dav': dav_app
            })

        container = tornado.wsgi.WSGIContainer(application)
        self.http_server = tornado.httpserver.HTTPServer(container)
        self.http_server.listen(port, hostname)
        if use_reloader:
            from tornado import autoreload
            autoreload.start()

        self.logger.info('webui running on %s:%s', hostname, port)
        self.ioloop = tornado.ioloop.IOLoop.current()
        self.ioloop.start()

    def quit(self):
        if hasattr(self, 'ioloop'):
            self.ioloop.add_callback(self.http_server.stop)
            self.ioloop.add_callback(self.ioloop.stop)
        self.logger.info('webui exiting...')


app = QuitableFlask('webui',
                    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                    template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.urandom(24)
app.jinja_env.line_statement_prefix = '#'
app.jinja_env.globals.update(builtins.__dict__)

app.config.update({
    'fetch': lambda x: tornado_fetcher.Fetcher(None, None, async=False).fetch(x),
    'taskdb': None,
    'projectdb': None,
    'scheduler_rpc': None,
    'queues': dict(),
})


def cdn_url_handler(error, endpoint, kwargs):
    if endpoint == 'cdn':
        path = kwargs.pop('path')
        # cdn = app.config.get('cdn', 'http://cdn.staticfile.org/')
        # cdn = app.config.get('cdn', '//cdnjs.cloudflare.com/ajax/libs/')
        cdn = app.config.get('cdn', '//cdnjscn.b0.upaiyun.com/libs/')
        return urljoin(cdn, path)
    else:
        exc_type, exc_value, tb = sys.exc_info()
        if exc_value is error:
            reraise(exc_type, exc_value, tb)
        else:
            raise error
app.handle_url_build_error = cdn_url_handler
