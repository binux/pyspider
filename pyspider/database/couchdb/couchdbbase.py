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

        url = self.base_url + "_all_dbs"
        res = requests.get(url, data=json.dumps({}), headers={"Content-Type": "application/json"}).json()
        for each in res:
            if each.startswith('_'):
                continue
            if each.startswith(self.database):
                self.projects.add(each[len(self.database)+1+len(prefix):])


    def create_database(self, name):
        url = self.base_url + name
        res = requests.put(url, headers={"Content-Type": "application/json"}).json()
        if name == "test_create_project":
            raise Exception
        return res


    def get_doc(self, db_name, doc_id):
        url = self.base_url + db_name + "/" + doc_id
        res = requests.get(url, headers={"Content-Type": "application/json"}).json()
        if "error" in res and res["error"] == "not_found":
            return None
        return res


    def get_docs(self, db_name, selector):
        url = self.base_url + db_name + "/_find"
        selector['use_index'] = self.index
        res = requests.post(url, data=json.dumps(selector), headers={"Content-Type": "application/json"}).json()
        if 'error' in res and res['error'] == 'not_found':
            return []
        return res['docs']


    def get_all_docs(self, db_name):
        return self.get_docs(db_name, {"selector": {}})


    def insert_doc(self, db_name, doc_id, doc):
        url = self.base_url + db_name + "/" + doc_id
        return requests.put(url, data=json.dumps(doc), headers={"Content-Type": "application/json"}).json()


    def update_doc(self, db_name, doc_id, new_doc):
        doc = self.get_doc(db_name, doc_id)
        if doc is None:
            return self.insert_doc(db_name, doc_id, new_doc)
        for key in new_doc:
            doc[key] = new_doc[key]
        url = self.base_url + db_name + "/" + doc_id
        return requests.put(url, data=json.dumps(doc), headers={"Content-Type": "application/json"}).json()


    def delete(self, url):
        return requests.delete(url, headers={"Content-Type": "application/json"}).json()

