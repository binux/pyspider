#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-6-3 11:29


import os
import re
import time
import base64
from six import BytesIO
from wsgidav.wsgidav_app import DEFAULT_CONFIG, WsgiDAVApp
from wsgidav.dav_provider import DAVProvider, DAVCollection, DAVNonCollection
from wsgidav.dav_error import DAVError, HTTP_NOT_FOUND, HTTP_FORBIDDEN
from pyspider.libs.utils import utf8, text
from .app import app


class ContentIO(BytesIO):
    def close(self):
        self.content = self.getvalue()
        BytesIO.close(self)


class ScriptResource(DAVNonCollection):
    def __init__(self, path, environ, app, project=None):
        super(ScriptResource, self).__init__(path, environ)

        self.app = app
        self.new_project = False
        self._project = project
        self.project_name = self.name
        self.writebuffer = None
        if self.project_name.endswith('.py'):
            self.project_name = self.project_name[:-len('.py')]

    @property
    def project(self):
        if self._project:
            return self._project
        projectdb = self.app.config['projectdb']
        if projectdb:
            self._project = projectdb.get(self.project_name)
        if not self._project:
            if projectdb.verify_project_name(self.project_name) and self.name.endswith('.py'):
                self.new_project = True
                self._project = {
                    'name': self.project_name,
                    'script': '',
                    'status': 'TODO',
                    'rate': self.app.config.get('max_rate', 1),
                    'burst': self.app.config.get('max_burst', 3),
                    'updatetime': time.time(),
                }
            else:
                raise DAVError(HTTP_FORBIDDEN)
        return self._project

    @property
    def readonly(self):
        projectdb = self.app.config['projectdb']
        if not projectdb:
            return True
        if 'lock' in projectdb.split_group(self.project.get('group')) \
                and self.app.config.get('webui_username') \
                and self.app.config.get('webui_password'):

            authheader = self.environ.get("HTTP_AUTHORIZATION")
            if not authheader:
                return True
            authheader = authheader[len("Basic "):]
            try:
                username, password = text(base64.b64decode(authheader)).split(':', 1)
            except Exception as e:
                self.app.logger.error('wrong api key: %r, %r', authheader, e)
                return True

            if username == self.app.config['webui_username'] \
                    and password == self.app.config['webui_password']:
                return False
            else:
                return True
        return False

    def getContentLength(self):
        return len(utf8(self.project['script']))

    def getContentType(self):
        return 'text/plain'

    def getLastModified(self):
        return self.project['updatetime']

    def getContent(self):
        return BytesIO(utf8(self.project['script']))

    def beginWrite(self, contentType=None):
        if self.readonly:
            self.app.logger.error('webdav.beginWrite readonly')
            return super(ScriptResource, self).beginWrite(contentType)
        self.writebuffer = ContentIO()
        return self.writebuffer

    def endWrite(self, withErrors):
        if withErrors:
            self.app.logger.error('webdav.endWrite error: %r', withErrors)
            return super(ScriptResource, self).endWrite(withErrors)
        if not self.writebuffer:
            return
        projectdb = self.app.config['projectdb']
        if not projectdb:
            return

        info = {
            'script': text(getattr(self.writebuffer, 'content', ''))
        }
        if self.project.get('status') in ('DEBUG', 'RUNNING'):
            info['status'] = 'CHECKING'

        if self.new_project:
            self.project.update(info)
            self.new_project = False
            return projectdb.insert(self.project_name, self.project)
        else:
            return projectdb.update(self.project_name, info)


class RootCollection(DAVCollection):
    def __init__(self, path, environ, app):
        super(RootCollection, self).__init__(path, environ)
        self.app = app
        self.projectdb = self.app.config['projectdb']

    def getMemberList(self):
        members = []
        for project in self.projectdb.get_all():
            project_name = utf8(project['name'])
            if not project_name.endswith('.py'):
                project_name += '.py'
            members.append(ScriptResource(
                os.path.join(self.path, project_name),
                self.environ,
                self.app,
                project
            ))
        return members

    def getMemberNames(self):
        members = []
        for project in self.projectdb.get_all(fields=['name', ]):
            project_name = utf8(project['name'])
            if not project_name.endswith('.py'):
                project_name += '.py'
            members.append(project_name)
        return members


class ScriptProvider(DAVProvider):
    def __init__(self, app):
        super(ScriptProvider, self).__init__()
        self.app = app

    def __repr__(self):
        return "pyspiderScriptProvider"

    def getResourceInst(self, path, environ):
        path = os.path.normpath(path).replace('\\', '/')
        if path in ('/', '.', ''):
            path = '/'
            return RootCollection(path, environ, self.app)
        else:
            return ScriptResource(path, environ, self.app)


config = DEFAULT_CONFIG.copy()
config.update({
    'mount_path': '/dav',
    'provider_mapping': {
        '/': ScriptProvider(app)
    },
    'user_mapping': {},
    'verbose': 1 if app.debug else 0,
    'dir_browser': {'davmount': False,
                    'enable': True,
                    'msmount': False,
                    'response_trailer': ''},
})
dav_app = WsgiDAVApp(config)
