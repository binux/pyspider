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
from six.moves import builtins, urllib
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from flask import Flask
from pyspider.fetcher import tornado_fetcher


if os.name == 'nt':
    import mimetypes
    mimetypes.add_type("text/css", ".css", True)


class TornadoFlask(Flask):
    """Flask object running with tornado ioloop"""

    @property
    def logger(self):
        return logger

    def run(self, host='0.0.0.0', port=5000):
        self.logger.info('webui starting on %s:%s', host, port)
        self.ioloop = IOLoop()
        http_server = HTTPServer(WSGIContainer(app), io_loop=self.ioloop)
        http_server.listen(port, host)
        self.ioloop.start()

    def quit(self):
        if hasattr(self, 'ioloop'):
            self.ioloop.stop()
        self.logger.info('webui exiting...')


app = TornadoFlask('webui',
                   static_folder=os.path.join(os.path.dirname(__file__), 'static'),
                   template_folder=os.path.join(os.path.dirname(__file__), 'templates'))
app.secret_key = os.urandom(24)
app.jinja_env.line_statement_prefix = '#'
app.jinja_env.globals.update(builtins.__dict__)

app.config.update({
    'fetch': lambda x: tornado_fetcher.Fetcher(None, None, async=False).fetch(x)[1],
    'taskdb': None,
    'projectdb': None,
    'scheduler_rpc': None,
})


def cdn_url_handler(error, endpoint, kwargs):
    if endpoint == 'cdn':
        path = kwargs.pop('path')
        # cdn = app.config.get('cdn', 'http://cdn.staticfile.org/')
        # cdn = app.config.get('cdn', '//cdnjs.cloudflare.com/ajax/libs/')
        cdn = app.config.get('cdn', '//cdnjscn.b0.upaiyun.com/libs/')
        return urllib.parse.urljoin(cdn, path)
    else:
        exc_type, exc_value, tb = sys.exc_info()
        if exc_value is error:
            reraise(exc_type, exc_value, tb)
        else:
            raise error
app.handle_url_build_error = cdn_url_handler
