from pyspider.database.base.resultdb import ResultDB as BaseResultDB
from .couchdbbase import SplitTableMixin


class ResultDB(SplitTableMixin, BaseResultDB):

    def __init__(self, url, database='resultdb'):
        raise NotImplementedError

    def _create_project(self, project):
        raise NotImplementedError

    def _parse(self, data):
        raise NotImplementedError

    def _stringify(self, data):
        raise NotImplementedError

    def save(self, project, taskid, url, result):
        raise NotImplementedError

    def select(self, project, fields=None, offset=0, limit=0):
        raise NotImplementedError

    def count(self, project):
        raise NotImplementedError

    def get(self, project, taskid, fields=None):
        raise NotImplementedError
