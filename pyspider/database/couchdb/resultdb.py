import time, json
from pyspider.database.base.resultdb import ResultDB as BaseResultDB
from .couchdbbase import SplitTableMixin


class ResultDB(SplitTableMixin, BaseResultDB):
    collection_prefix = ''

    def __init__(self, url, database='resultdb', username=None, password=None):
        self.username = username
        self.password = password
        self.base_url = url
        self.url = url + database + "/"
        self.database = database

        super().__init__()
        self.create_database(database)
        self.index = None

    def _get_collection_name(self, project):
        return self.database + "_" + self._collection_name(project)

    def _create_project(self, project):
        collection_name = self._get_collection_name(project)
        self.create_database(collection_name)
        # create index
        payload = {
            'index': {
                'fields': ['taskid']
            },
            'name': collection_name
        }

        res = self.session.post(self.base_url + collection_name + "/_index", json=payload).json()
        self.index = res['id']
        self._list_project()

    def save(self, project, taskid, url, result):
        if project not in self.projects:
            self._create_project(project)
        collection_name = self._get_collection_name(project)
        obj = {
            'taskid': taskid,
            'url': url,
            'result': result,
            'updatetime': time.time(),
        }
        return self.update_doc(collection_name, taskid, obj)

    def select(self, project, fields=None, offset=0, limit=0):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        offset = offset or 0
        limit = limit or 0
        collection_name = self._get_collection_name(project)
        if fields is None:
            fields = []
        if limit == 0:
            sel = {
                'selector': {},
                'fields': fields,
                'skip': offset
            }
        else:
            sel = {
              'selector': {},
              'fields': fields,
              'skip': offset,
              'limit': limit
            }
        for result in self.get_docs(collection_name, sel):
            yield result

    def count(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._get_collection_name(project)
        return len(self.get_all_docs(collection_name))

    def get(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._get_collection_name(project)
        if fields is None:
            fields = []
        sel = {
            'selector': {'taskid': taskid},
            'fields': fields
        }
        ret = self.get_docs(collection_name, sel)
        if len(ret) == 0:
            return None
        return ret[0]

    def drop_database(self):
        return self.delete(self.url)

    def drop(self, project):
        # drop the project
        collection_name = self._get_collection_name(project)
        url = self.base_url + collection_name
        return self.delete(url)