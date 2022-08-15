import json, time
from pyspider.database.base.taskdb import TaskDB as BaseTaskDB
from .couchdbbase import SplitTableMixin


class TaskDB(SplitTableMixin, BaseTaskDB):
    collection_prefix = ''

    def __init__(self, url, database='taskdb', username=None, password=None):
        self.username = username
        self.password = password
        self.base_url = url
        self.url = url + database + "/"
        self.database = database
        self.index = None

        super().__init__()

        self.create_database(database)
        self.projects = set()
        self._list_project()

    def _get_collection_name(self, project):
        return self.database + "_" + self._collection_name(project)

    def _create_project(self, project):
        collection_name = self._get_collection_name(project)
        self.create_database(collection_name)
        # create index
        payload = {
            'index': {
                'fields': ['status', 'taskid']
            },
            'name': collection_name
        }
        res = self.session.post(self.base_url + collection_name + "/_index", json=payload).json()
        self.index = res['id']
        self._list_project()

    def load_tasks(self, status, project=None, fields=None):
        if not project:
            self._list_project()
        if fields is None:
            fields = []
        if project:
            projects = [project, ]
        else:
            projects = self.projects
        for project in projects:
            collection_name = self._get_collection_name(project)
            for task in self.get_docs(collection_name, {"selector": {"status": status}, "fields": fields}):
                yield task

    def get_task(self, project, taskid, fields=None):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        if fields is None:
            fields = []
        collection_name = self._get_collection_name(project)
        ret = self.get_docs(collection_name, {"selector": {"taskid": taskid}, "fields": fields})
        if len(ret) == 0:
            return None
        return ret[0]

    def status_count(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return {}
        collection_name = self._get_collection_name(project)

        def _count_for_status(collection_name, status):
            total = len(self.get_docs(collection_name, {"selector": {'status': status}}))
            return {'total': total, "_id": status} if total else None

        c = collection_name
        ret = filter(lambda x: x,map(lambda s: _count_for_status(c, s), [self.ACTIVE, self.SUCCESS, self.FAILED]))

        result = {}
        if isinstance(ret, dict):
            ret = ret.get('result', [])
        for each in ret:
            result[each['_id']] = each['total']
        return result

    def insert(self, project, taskid, obj={}):
        if project not in self.projects:
            self._create_project(project)
        obj = dict(obj)
        obj['taskid'] = taskid
        obj['project'] = project
        obj['updatetime'] = time.time()
        return self.update(project, taskid, obj=obj)

    def update(self, project, taskid, obj={}, **kwargs):
        obj = dict(obj)
        obj.update(kwargs)
        obj['updatetime'] = time.time()
        collection_name = self._get_collection_name(project)
        return self.update_doc(collection_name, taskid, obj)

    def drop_database(self):
        return self.delete(self.url)

    def drop(self, project):
        collection_name = self._get_collection_name(project)
        url = self.base_url + collection_name
        return self.delete(url)