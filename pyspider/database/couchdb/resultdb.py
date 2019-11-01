import time, json, requests
from pyspider.database.base.resultdb import ResultDB as BaseResultDB
from .couchdbbase import SplitTableMixin


class ResultDB(SplitTableMixin, BaseResultDB):
    collection_prefix = ''

    def __init__(self, url, database='resultdb'):
        self.base_url = url
        # TODO: Add collection_prefix
        self.url = url + database + "/"
        self.database = database
        self.create_database(database)

    def _get_collection_name(self, project):
        return self.database + "_" + self._collection_name(project)

    def _create_project(self, project):
        collection_name = self._get_collection_name(project)
        self.create_database(collection_name)
        #self.database[collection_name].ensure_index('taskid')
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
        #return self.database[collection_name].update(
        #    {'taskid': taskid}, {"$set": self._stringify(obj)}, upsert=True
        #)

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
        #for result in self.database[collection_name].find({}, fields, skip=offset, limit=limit):
        #    yield self._parse(result)

    def count(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._get_collection_name(project)
        return len(self.get_all_docs(collection_name))
        #return self.database[collection_name].count()

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
        #ret = self.database[collection_name].find_one({'taskid': taskid}, fields)
        if ret is None or len(ret) == 0:
            return None
        return ret[0]

    def drop_database(self):
        res = requests.delete(self.url, headers={"Content-Type": "application/json"}).json()
        print('[couchdb resultdb drop_database] - url: {} res: {}'.format(self.url, res))
        return res

    def drop(self, project):
        # drop the project
        collection_name = self._get_collection_name(project)
        res = requests.delete(self.base_url+collection_name, headers={"Content-Type": "application/json"}).json()
        print('[couchdb resultdb drop] - url: {} res: {}'.format(self.url, res))
        return res