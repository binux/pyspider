# -*- encoding: utf-8 -*-
import datetime
from jinja2 import Template


def get_sample_task():
    from .task import default_task
    return default_task


def get_sample_handler(project, start_url=None, date=None):
    from pyspider.libs.samples import handler
    import inspect
    source = inspect.getsource(handler)
    tp = Template(source)
    if date is None:
        date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not start_url:
        start_url = '__START_URL__'
    res = tp.render(DATE=date, PROJECT_NAME=project, START_URL=start_url)
    return res
