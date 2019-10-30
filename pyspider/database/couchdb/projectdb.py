import time, requests, json
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB


class ProjectDB(BaseProjectDB):
    __collection_name__ = 'projectdb'

    def __init__(self, url, database='projectdb'):
        self.base_url = url
        self.url = url + database + "/"
        self.database = database
        self.insert('', {})

    def _default_fields(self, each):
        if each is None:
            return each
        each.setdefault('group')
        each.setdefault('status', 'TODO')
        each.setdefault('script', '')
        each.setdefault('comments')
        each.setdefault('rate', 0)
        each.setdefault('burst', 0)
        each.setdefault('updatetime', 0)
        return each

    def insert(self, name, obj={}):
        url = self.url + name
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        res = requests.put(url, data = json.dumps(obj), headers = {"Content-Type": "application/json"}).json()
        print('[couchdb projectdb insert] - url: {} data: {} res: {}'.format(url, json.dumps(obj), res))
        return res

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        self.insert(name, obj)

    def get_all(self, fields=None):
        if fields is None:
            fields = []
        payload = {
            "selector": {},
            "fields": fields
        }
        url = self.url + "_find"
        res = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}).json()
        print('[couchdb projectdb get_all] - url: {} res: {}'.format(url, res))
        return res['docs']

    def get(self, name, fields=None):
        if fields is None:
            fields = []
        payload = {
            "selector": {"name": name},
            "fields": fields,
            "limit": 1
        }
        url = self.url + "_find"
        res = requests.post(url, data=json.dumps(payload), headers={"Content-Type": "application/json"}).json()
        print('[couchdb projectdb get] - url: {} res: {}'.format(url, res))
        return res['docs'][0]

    def check_update(self, timestamp, fields=None):
        if fields is None:
            fields = []
        for project in self.get_all(fields=('updatetime', 'name')):
            if project['updatetime'] > timestamp:
                project = self.get(project['name'], fields)
                yield self._default_fields(project)

    def drop(self, name):
        doc = self.get(name)
        url = self.url + name + "/" + doc["_rev"]
        res = requests.delete(url, headers={"Content-Type": "application/json"}).json()
        print('[couchdb projectdb drop] - url: {} res: {}'.format(url, res))
        return res

    def drop_database(self):
        res = requests.delete(self.base_url, headers={"Content-Type": "application/json"}).json()
        print('[couchdb projectdb drop_database] - url: {} res: {}'.format(self.base_url, res))
        return res

