#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-09-12 22:39:57
# form requests&tornado

import UserDict
import cookielib
from urlparse import urlparse
from tornado import httpclient, httputil

class MockRequest(object):
    """Wraps a `tornado.httpclient.HTTPRequest` to mimic a `urllib2.Request`.

    The code in `cookielib.CookieJar` expects this interface in order to correctly
    manage cookie policies, i.e., determine whether a cookie can be set, given the
    domains of the request and the cookie.

    The original request object is read-only. The client is responsible for collecting
    the new headers via `get_new_headers()` and interpreting them appropriately. You
    probably want `get_cookie_header`, defined below.
    """

    def __init__(self, request):
        self._r = request
        self._new_headers = {}

    def get_type(self):
        return urlparse(self._r.url).scheme

    def get_host(self):
        return urlparse(self._r.url).netloc

    def get_origin_req_host(self):
        return self.get_host()

    def get_full_url(self):
        return self._r.url

    def is_unverifiable(self):
        # unverifiable == redirected
        return False

    def has_header(self, name):
        return name in self._r.headers or name in self._new_headers

    def get_header(self, name, default=None):
        return self._r.headers.get(name, self._new_headers.get(name, default))

    def add_header(self, key, val):
        """cookielib has no legitimate use for this method; add it back if you find one."""
        raise NotImplementedError("Cookie headers should be added with add_unredirected_header()")

    def add_unredirected_header(self, name, value):
        self._new_headers[name] = value

    def get_new_headers(self):
        return self._new_headers


class MockResponse(object):
    """Wraps a `tornado.httputil.HTTPHeaders` to mimic a `urllib.addinfourl`.

    ...what? Basically, expose the parsed HTTP headers from the server response
    the way `cookielib` expects to see them.
    """

    def __init__(self, headers):
        """Make a MockResponse for `cookielib` to read.

        :param headers: a httplib.HTTPMessage or analogous carrying the headers
        """
        self._headers = headers

    def info(self):
        return self._headers

    def getheaders(self, name):
        self._headers.get_list(name)

def create_cookie(name, value, **kwargs):
    """Make a cookie from underspecified parameters.

    By default, the pair of `name` and `value` will be set for the domain ''
    and sent on every request (this is sometimes called a "supercookie").
    """
    result = dict(
        version=0,
        name=name,
        value=value,
        port=None,
        domain='',
        path='/',
        secure=False,
        expires=None,
        discard=True,
        comment=None,
        comment_url=None,
        rest={'HttpOnly': None},
        rfc2109=False,
        )

    badargs = set(kwargs) - set(result)
    if badargs:
        err = 'create_cookie() got unexpected keyword arguments: %s'
        raise TypeError(err % list(badargs))

    result.update(kwargs)
    result['port_specified'] = bool(result['port'])
    result['domain_specified'] = bool(result['domain'])
    result['domain_initial_dot'] = result['domain'].startswith('.')
    result['path_specified'] = bool(result['path'])

    return cookielib.Cookie(**result)

def remove_cookie_by_name(cookiejar, name, domain=None, path=None):
    """Unsets a cookie by name, by default over all domains and paths.

    Wraps CookieJar.clear(), is O(n).
    """
    clearables = []
    for cookie in cookiejar:
        if cookie.name == name:
            if domain is None or domain == cookie.domain:
                if path is None or path == cookie.path:
                    clearables.append((cookie.domain, cookie.path, cookie.name))

    for domain, path, name in clearables:
        cookiejar.clear(domain, path, name)

class CookieSession(cookielib.CookieJar, UserDict.DictMixin):
    def extract_cookies_to_jar(self, request, response):
        """Extract the cookies from the response into a CookieJar.

        :param jar: cookielib.CookieJar (not necessarily a RequestsCookieJar)
        :param request: our own requests.Request object
        :param response: urllib3.HTTPResponse object
        """
        # the _original_response field is the wrapped httplib.HTTPResponse object,
        req = MockRequest(request)
        # pull out the HTTPMessage with the headers and put it in the mock:
        headers = response
        if not hasattr(headers, "keys"):
            headers = headers.headers
        headers.getheaders = headers.get_list
        res = MockResponse(headers)
        self.extract_cookies(res, req)

    def get_cookie_header(self, request):
        """Produce an appropriate Cookie header string to be sent with `request`, or None."""
        r = MockRequest(request)
        self.add_cookie_header(r)
        return r.get_new_headers().get('Cookie')

    def __getitem__(self, name):
        if isinstance(name, cookielib.Cookie):
            return name.value
        for cookie in cookielib.CookieJar.__iter__(self):
            if cookie.name == name:
                return cookie.value
        raise KeyError(name)

    def __setitem__(self, name, value):
        if value is None:
            remove_cookie_by_name(self, name)
        else:
            self.set_cookie(create_cookie(name, value))

    def __delitem__(self, name):
        remove_cookie_by_name(self, name)

    def keys(self):
        result = []
        for cookie in cookielib.CookieJar.__iter__(self):
            result.append(cookie.name)
        return result

    def to_dict(self):
        result = {}
        for key in self.keys():
            result[key] = self.get(key)
        return result

class CookieTracker:
    def __init__(self):
        self.headers = httputil.HTTPHeaders()

    def get_header_callback(self):
        _self = self
        def header_callback(header):
            header = header.strip()
            if header.starswith("HTTP/"):
                return
            if not header:
                return
            _self.headers.parse_line(header)
        return header_callback
