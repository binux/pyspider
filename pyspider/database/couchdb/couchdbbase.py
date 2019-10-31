import time, requests, json


class SplitTableMixin(object):
    UPDATE_PROJECTS_TIME = 10 * 60

    def _collection_name(self, project):
        if self.collection_prefix:
            return "%s_%s" % (self.collection_prefix, project)
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

        res = requests.get(self.base_url+"_all_dbs", data=json.dumps({}), headers={"Content-Type": "application/json"}).json()
        for each in res:
            if each.startswith('_'):
                continue
            if each.startswith(prefix):
                self.projects.add(each[len(prefix):])


    def create_database(self, name):
        url = self.base_url + name
        res = requests.put(url, data=json.dumps({}), headers={"Content-Type": "application/json"}).json()
        print('[couchdbbase create_database] - url: {} res: {}'.format(url, res))
        return res


    def get_docs(self, db_name, selector):
        url = self.base_url + db_name
        payload = {
            "selector": selector
        }
        res = requests.post(url+"_find", data=json.dumps(payload), headers={"Content-Type": "application/json"}).json()
        print('[couchdbbase get_docs] - url: {} payload: {} res: {}'.format(url, payload, res))
        return res['docs']


    def get_all_docs(self, db_name):
        url = self.base_url + db_name
        res = requests.get(url, headers={"Content-Type": "application/json"}).json()
        print('[couchdbbase get_all_docs] - url: {} res: {}'.format(url, res))
        return res['docs']


    def update_doc(self, db_name, selector, new_doc):
        doc = self.get_docs(db_name, selector)
        if doc is None:
            return
        url = self.base_url + db_name
        for key in new_doc:
            doc[key] = new_doc[key]
        res = requests.put(url, data=json.dumps(doc), headers={"Content-Type": "application/json"}).json()
        print('[couchdbbase update_doc] - url: {} res: {}'.format(url, res))
        return res



    def drop(self, project):
        if project not in self.projects:
            self._list_project()
        if project not in self.projects:
            return
        collection_name = self._collection_name(project)
        res = requests.delete(self.base_url+collection_name, headers={"Content-Type": "application/json"}).json()
        self._list_project()


