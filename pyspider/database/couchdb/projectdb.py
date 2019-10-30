import time, requests, json
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB


class ProjectDB(BaseProjectDB):
    __collection_name__ = 'projectdb'

    def __init__(self, url, database='projectdb'):
        self.url = url
        self.database = database

        if self.url[-1] != "/":
            self.url = self.url + "/"
        self.url = self.url + self.database

        self.insert('', {})

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
        url = self.url + self.__collection_name__ + "/" + name
        obj = dict(obj)
        obj['name'] = name
        obj['updatetime'] = time.time()
        print("[couchdb insert] - insert url: {} obj: {}".format(url, json.dumps(obj)))
        return requests.put(url, data = json.dumps(obj), headers = {"Content-Type": "application/json"})

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        self.insert(name, obj)

    def get_all(self, fields=None):
        payload = {
            "selector": {},
            "fields": fields
        }
        return requests.post(self.url+"_find", data=payload)

    def get(self, name, fields=None):
        payload = {
            "selector": {"name": name},
            "fields": fields,
            "limit": 1
        }
        return requests.post(self.url + "_find", data=payload)

    def check_update(self, timestamp, fields=None):
        for project in self.get_all(fields=('updatetime', 'name')):
            if project['updatetime'] > timestamp:
                project = self.get(project['name'], fields)
                yield self._default_fields(project)

    def drop(self, name):
        doc = json.loads(self.get(name))
        return requests.delete(self.url+name+"/"+doc["_rev"])

