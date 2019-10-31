import time, requests, json


class SplitTableMixin(object):

    def _collection_name(self, project):
        if self.collection_prefix:
            return "%s.%s" % (self.collection_prefix, project)
        else:
            return project


    @property
    def projects(self):
        if time.time() - getattr(self, '_last_update_projects', 0) > self.UPDATE_PROJECTS_TIME:
            self._list_project()
        return self._projects


    @projects.setter
    def projects(self, value):
        self._projects = value


    def _list_project(self):
        self._last_update_projects = time.time()
        self.projects = set()
        if self.collection_prefix:
            prefix = "%s." % self.collection_prefix
        else:
            prefix = ''

        res = requests.get(url, data=json.dumps({}), headers={"Content-Type": "application/json"}).json()
        for each in res:
            if each.startswith('_'):
                continue
            if each.startswith(prefix):
                self.projects.add(each[len(prefix):])


    def drop(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        self.database[collection_name].drop()
        self._list_project()

