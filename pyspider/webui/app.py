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


class TornadoFlask(Flask):
    """Flask object running with tornado ioloop"""

    @property
    def logger(self):
        return logger

    def run(self, host=None, port=None, debug=None, **options):
        from werkzeug.serving import make_server, run_with_reloader

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

        #run_simple(host, port, self, **options)
        hostname = host
        port = port
        application = self
        use_reloader = self.debug
        use_debugger = self.debug

        if use_debugger:
            from werkzeug.debug import DebuggedApplication
            application = DebuggedApplication(application, True)

        def inner():
            self.server = make_server(hostname, port, application)
            self.server.serve_forever()

        if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
            display_hostname = hostname != '*' and hostname or 'localhost'
            if ':' in display_hostname:
                display_hostname = '[%s]' % display_hostname
            self.logger.info('webui running on http://%s:%d/', display_hostname, port)

        if use_reloader:
            run_with_reloader(inner)
        else:
            inner()

    def quit(self):
        if hasattr(self, 'server'):
            self.server.shutdown_signal = True
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
        return urljoin(cdn, path)
    else:
        exc_type, exc_value, tb = sys.exc_info()
        if exc_value is error:
            reraise(exc_type, exc_value, tb)
        else:
            raise error
app.handle_url_build_error = cdn_url_handler
