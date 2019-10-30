from pyspider.database.base.taskdb import TaskDB as BaseTaskDB
from .couchdbbase import SplitTableMixin


class TaskDB(SplitTableMixin, BaseTaskDB):

    def __init__(self, url, database='taskdb'):
        raise NotImplementedError

    def _create_project(self, project):
        raise NotImplementedError

    def _parse(self, data):
        raise NotImplementedError

    def _stringify(self, data):
        raise NotImplementedError

    def load_tasks(self, status, project=None, fields=None):
        raise NotImplementedError

    def get_task(self, project, taskid, fields=None):
        raise NotImplementedError

    def status_count(self, project):
        raise NotImplementedError

    def insert(self, project, taskid, obj={}):
        raise NotImplementedError

    def update(self, project, taskid, obj={}, **kwargs):
        raise NotImplementedError