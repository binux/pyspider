#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Created on __DATE__

from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    """
    A Sample Handler
    """
    crawl_config = {
    }

    @every(minutes=24 * 60, seconds=0)
    def on_start(self):
        """Called when click the `run` button on dashboard, re-execute every 24 hours"""

        self.crawl('http://scrapy.org/', callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http://"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }
