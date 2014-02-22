#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 14:02:21

from libs.base_handler import BaseHandler, catch_status_code_error

class TestHandler(BaseHandler):
    def hello(self):
        return "hello world!"

    def echo(self, response):
        return response.content

    def saved(self, response, saved):
        return saved

    def echo_task(self, response, saved, task):
        return task['project']

    @catch_status_code_error
    def catch_status_code(self, response):
        return response.status_code

    def raise_exception(self):
        logger.info("info")
        logger.warning("warning")
        logger.error("error")
        raise Exception('exception')

    def add_task(self, response):
        self.crawl('http://www.google.com', callback='echo', params={'wd': u'中文'})
        self.send_message('some_project', {'some': 'message'})
