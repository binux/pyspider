#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Created on __DATE__

from libs.pprint import pprint
from libs.base_handler import *

class Handler(BaseHandler):
    '''
    this is a sample handler
    '''
    def on_start(self):
        self.crawl('http://www.baidu.com/', callback=self.index_page)

    def index_page(self, response):
        for each in response.doc('a[href^="http://"]').items():
            self.crawl(each.attr.href, callback=self.index_page)
        return response.doc('title').text()

    def on_result(self, result, response, task):
        if not result:
            return
        if self.__env__.get('debugger'):
            pprint(result)
        super(Handler, self).on_result(result, response, task)
