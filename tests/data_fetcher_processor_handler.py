#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-01-18 14:12:55

from pyspider.libs.base_handler import *

class Handler(BaseHandler):

    @not_send_status
    def not_send_status(self, response):
        self.crawl('http://www.baidu.com/')
        return response.text

    def url_deduplicated(self, response):
        self.crawl('http://www.baidu.com/')
        self.crawl('http://www.google.com/')
        self.crawl('http://www.baidu.com/')
        self.crawl('http://www.google.com/')
        self.crawl('http://www.google.com/')

    @catch_status_code_error
    def catch_http_error(self, response):
        self.crawl('http://www.baidu.com/')
        return response.status_code

    def json(self, response):
        return response.json

    def html(self, response):
        return response.doc('h1').text()

    def links(self, response):
        self.crawl([x.attr.href for x in response.doc('a').items()], callback=self.links)

    def cookies(self, response):
        return response.cookies

    def get_save(self, response):
        return response.save

    def get_process_save(self, response):
        return self.save

    def set_process_save(self, response):
        self.save['roy'] = 'binux'

class IgnoreHandler(BaseHandler):
    pass

__handler_cls__ = Handler
