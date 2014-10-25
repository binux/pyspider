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
        self.crawl('http://www.baidu.com/', callback=self.index_page)

    @every(minutes=1, seconds=10)
    def some_cronjob(self):
        self.on_start()

    @config(age=10*24*60*60)
    def index_page(self, response):
        for each in response.doc('a[href^="http://"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    def detail_page(self, response):
        return {
                "url": response.url,
                "title": response.doc('title').text(),
                }
