import time, json, requests
from requests.auth import HTTPBasicAuth
from pyspider.database.base.resultdb import ResultDB as BaseResultDB
from .couchdbbase import SplitTableMixin


class ResultDB(SplitTableMixin, BaseResultDB):
    collection_prefix = ''

    def __init__(self, url, database='resultdb', username='username', password='password'):
        self.username = username
        self.password = password

        self.base_url = url
        self.url = url + database + "/"
        self.database = database
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

        res = requests.post(self.base_url + collection_name + "/_index",
                            data=json.dumps(payload),
                            headers={"Content-Type": "application/json"},
                            auth=HTTPBasicAuth(self.username, self.password)).json()

        print("[couchdb resultdb _create_project] - creating index. payload: {} res: {}".format(json.dumps(payload), res))
        self.index = res['id']
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