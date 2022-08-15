
#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 14:02:21

import time
from pyspider.libs.base_handler import BaseHandler, catch_status_code_error, every

class IgnoreHandler(object):
    pass

class TestHandler(BaseHandler):
    retry_delay = {
        1: 10,
        '': -1
    }

    def hello(self):
        return "hello world!"

    def echo(self, response):
        return response.content

    def saved(self, response):
        return response.save

    def echo_task(self, response, task):
        return task['project']

    @catch_status_code_error
    def catch_status_code(self, response):
        return response.status_code

    def raise_exception(self):
        print('print')
        logger.info("info")
        logger.warning("warning")
        logger.error("error")
        raise Exception('exception')

    def add_task(self, response):
        self.crawl('http://www.google.com', callback='echo', params={'wd': u'中文'})
        self.send_message('some_project', {'some': 'message'})

    @every
    def on_cronjob1(self, response):
        logger.info('on_cronjob1')

    @every(seconds=10)
    def on_cronjob2(self, response):
        logger.info('on_cronjob2')

    def generator(self, response):
        yield "a"
        yield "b"

    def sleep(self, response):
        time.sleep(response.save)

