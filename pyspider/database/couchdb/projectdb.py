import time, requests, json
from pyspider.database.base.projectdb import ProjectDB as BaseProjectDB


class ProjectDB(BaseProjectDB):
    __collection_name__ = 'projectdb'

    def __init__(self, url, database='projectdb'):
        self.url = url
        self.database = database
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
        res = requests.put(url, data = json.dumps(obj), headers = {"Content-Type": "application/json"}).json()
        print('[couchdb projectdb insert] - url: {} res: {}'.format(url,res))
        return res

    def update(self, name, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        self.insert(name, obj)

    def get_all(self, fields=None):
        payload = {
            "selector": {},
            "fields": fields
        }
        res = requests.post(self.url+"_find", data=json.dumps(payload)).json()
        print('[couchdb projectdb get_all] - url: {} res: {}'.format(self.url, res))
        return res


    def get(self, name, fields=None):
        payload = {
            "selector": {"name": name},
            "fields": fields,
            "limit": 1
        }
        res = requests.post(self.url + "_find", data=json.dumps(payload)).json()
        print('[couchdb projectdb get] - url: {} res: {}'.format(self.url, res))
        return res

    def check_update(self, timestamp, fields=None):
        for project in self.get_all(fields=('updatetime', 'name')):
            if project['updatetime'] > timestamp:
                project = self.get(project['name'], fields)
                yield self._default_fields(project)

    def drop(self, name):
        doc = self.get(name)
        res = requests.delete(self.url+name+"/"+doc["_rev"]).json()
        print('[couchdb projectdb drop] - url: {} res: {}'.format(self.url, res))
        return res

