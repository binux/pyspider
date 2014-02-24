#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Created on __DATE__

from libs.base_handler import *

class Handler(BaseHandler):
    '''
    this is a sample handler
    '''
    def on_start(self):
        self.crawl('http://www.baidu.com/')

    def index_page(self, response):
        return response.content
