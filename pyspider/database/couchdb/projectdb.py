import time, requests, json
from requests.auth import HTTPBasicAuth
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB


class ProjectDB(BaseProjectDB):
    __collection_name__ = 'projectdb'

    def __init__(self, url, database='projectdb', username=None, password=None):
        self.username = username
        self.password = password
        self.url = url + self.__collection_name__ + "_" + database + "/"
        self.database = database

        self.session = requests.session()
        if username:
            self.session.auth = HTTPBasicAuth(self.username, self.password)
        self.session.headers.update({'Content-Type': 'application/json'})

        # Create the db
        res = self.session.put(self.url).json()
        if 'error' in res and res['error'] == 'unauthorized':
            raise Exception(
                "Supplied credentials are incorrect. Reason: {} for User: {} Password: {}".format(res['reason'],
                                                                                                  self.username,
                                                                                                  self.password))
        # create index
        payload = {
            'index': {
                'fields': ['name']
            },
            'name': self.__collection_name__ + "_" + database
        }
        res = self.session.post(self.url + "_index", json=payload).json()
        self.index = res['id']

    def _default_fields(self, each):
        if each is None:
            return each
        each.setdefault('group', None)
        each.setdefault('status', 'TODO')
        each.setdefault('script', '')
        each.setdefault('comments', None)
        each.setdefault('rate', 0)
        each.setdefault('burst', 0)
        each.setdefault('updatetime', 0)
        return each

    def insert(self, name, obj={}):
        url = self.url + name
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        res = self.session.put(url, json=obj).json()
        return res

    def update(self, name, obj={}, **kwargs):
        # object contains the fields to update and their new values
        update = self.get(name) # update will contain _rev
        if update is None:
            return None
        obj = dict(obj)
        obj['updatetime'] = time.time()
        obj.update(kwargs)
        for key in obj:
            update[key] = obj[key]
        return self.insert(name, update)

    def get_all(self, fields=None):
        if fields is None:
            fields = []
        payload = {
            "selector": {},
            "fields": fields,
            "use_index": self.index
        }
        url = self.url + "_find"
        res = self.session.post(url, json=payload).json()
        for doc in res['docs']:
            yield self._default_fields(doc)

    def get(self, name, fields=None):
        if fields is None:
            fields = []
        payload = {
            "selector": {"name": name},
            "fields": fields,
            "limit": 1,
            "use_index": self.index
        }
        url = self.url + "_find"
        res = self.session.post(url, json=payload).json()
        if len(res['docs']) == 0:
            return None
        return self._default_fields(res['docs'][0])

    def check_update(self, timestamp, fields=None):
        if fields is None:
            fields = []
        for project in self.get_all(fields=('updatetime', 'name')):
            if project['updatetime'] > timestamp:
                project = self.get(project['name'], fields)
                yield self._default_fields(project)

    def drop(self, name):
        doc = self.get(name)
        payload = {"rev": doc["_rev"]}
        url = self.url + name
        return self.session.delete(url, params=payload).json()

    def drop_database(self):
        return self.session.delete(self.url).json()
