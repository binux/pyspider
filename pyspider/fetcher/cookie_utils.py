#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-14 09:07:11

from requests.cookies import MockRequest


class MockResponse(object):

    def __init__(self, headers):
        self._headers = headers

    def info(self):
        return self

    def getheaders(self, name):
        """make cookie python 2 version use this method to get cookie list"""
        return self._headers.get_list(name)

    def get_all(self, name, default=None):
        """make cookie python 3 version use this instead of getheaders"""
        if default is None:
            default = []
        return self._headers.get_list(name) or default


def extract_cookies_to_jar(jar, request, response):
    req = MockRequest(request)
    res = MockResponse(response)
    jar.extract_cookies(res, req)
