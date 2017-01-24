#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-6-3 11:29


import os
import time
import base64
import six
from six import BytesIO
from wsgidav.wsgidav_app import DEFAULT_CONFIG, WsgiDAVApp
from wsgidav.dav_provider import DAVProvider, DAVCollection, DAVNonCollection
from wsgidav.dav_error import DAVError, HTTP_FORBIDDEN
from pyspider.libs.utils import utf8, text
from .app import app


def check_user(environ):
    authheader = environ.get("HTTP_AUTHORIZATION")
    if not authheader:
        return False
    authheader = authheader[len("Basic "):]
    try:
        username, password = text(base64.b64decode(authheader)).split(':', 1)
    except Exception as e:
        app.logger.error('wrong api key: %r, %r', authheader, e)
        return False

    if username == app.config['webui_username'] \
            and password == app.config['webui_password']:
        return True
    else:
        return False


class ContentIO(BytesIO):
    def close(self):
        self.content = self.getvalue()
        BytesIO.close(self) #old class


class ScriptResource(DAVNonCollection):
    def __init__(self, path, environ, app, project=None):
        super(ScriptResource, self).__init__(path, environ)

        self.app = app
        self.new_project = False
        self._project = project
        self.project_name = text(self.name)
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
            if projectdb.verify_project_name(self.project_name) and text(self.name).endswith('.py'):
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
            return not check_user(self.environ)
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
            project_name = project['name']
            if not project_name.endswith('.py'):
                project_name += '.py'
            native_path = os.path.join(self.path, project_name)
            native_path = text(native_path) if six.PY3 else utf8(native_path)
            members.append(ScriptResource(
                native_path,
                self.environ,
                self.app,
                project
            ))
        return members

    def getMemberNames(self):
        members = []
        for project in self.projectdb.get_all(fields=['name', ]):
            project_name = project['name']
            if not project_name.endswith('.py'):
                project_name += '.py'
            members.append(utf8(project_name))
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


class NeedAuthController(object):
    def __init__(self, app):
        self.app = app

    def getDomainRealm(self, inputRelativeURL, environ):
        return 'need auth'

    def requireAuthentication(self, realmname, environ):
        return self.app.config.get('need_auth', False)

    def isRealmUser(self, realmname, username, environ):
        return username == self.app.config.get('webui_username')

    def getRealmUserPassword(self, realmname, username, environ):
        return self.app.config.get('webui_password')

    def authDomainUser(self, realmname, username, password, environ):
        return username == self.app.config.get('webui_username') \
            and password == self.app.config.get('webui_password')


config = DEFAULT_CONFIG.copy()
config.update({
    'mount_path': '/dav',
    'provider_mapping': {
        '/': ScriptProvider(app)
    },
    'domaincontroller': NeedAuthController(app),
    'verbose': 1 if app.debug else 0,
    'dir_browser': {'davmount': False,
                    'enable': True,
                    'msmount': False,
                    'response_trailer': ''},
})
dav_app = WsgiDAVApp(config)
