#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-02 11:16:02

import json
import chardet
from requests.structures import CaseInsensitiveDict
from requests.utils import get_encoding_from_headers, get_encodings_from_content
from requests import HTTPError

class Response(object):
    def __init__(self):
        self.status_code = None
        self.url = None
        self.headers = CaseInsensitiveDict()
        self.content = ''
        self.cookies = {}
        self.error = None

    def __repr__(self):
       return '<Response [%d]>' % self.status_code

    def __bool__(self):
        """Returns true if :attr:`status_code` is 'OK'."""
        return self.ok

    def __nonzero__(self):
        """Returns true if :attr:`status_code` is 'OK'."""
        return self.ok

    @property
    def ok(self):
        try:
            self.raise_for_status()
        except RequestException:
            return False
        return True

    @property
    def encoding(self):
        if hasattr(self, '_encoding'):
            return self._encoding

        # Try charset from content-type
        encoding = get_encoding_from_headers(self.headers)
        if encoding == 'ISO-8859-1':
            encoding = None

        # Try charset from content
        if not encoding:
            encoding = get_encodings_from_content(self.content)
            encoding = encoding and encoding[0] or None

        # Fallback to auto-detected encoding.
        if not encoding and chardet is not None:
            encoding = chardet.detect(self.content)['encoding']

        if encoding and encoding.lower() == 'gb2312':
            encoding = 'gb18030'

        self._encoding = encoding or 'utf-8'
        return self._encoding

    @encoding.setter
    def encoding(self, value):
        self._encoding = value
        self._text = None

    @property
    def text(self):
        """Content of the response, in unicode.

        if Response.encoding is None and chardet module is available, encoding
        will be guessed.
        """
        if hasattr(self, '_text') and self._text:
            return self._text
        if not self.content:
            return u''
        if isinstance(self.content, unicode):
            return self.content

        content = None
        encoding = self.encoding

        # Decode unicode from given encoding.
        try:
            content = self.content.decode(encoding, 'replace')
        except LookupError:
            # A LookupError is raised if the encoding was not found which could
            # indicate a misspelling or similar mistake.
            #
            # So we try blindly encoding.
            content = self.content.decode('utf-8', 'replace')

        self._text = content
        return content

    @property
    def json(self):
        """Returns the json-encoded content of a request, if any."""
        try:
            return json.loads(self.text or self.content)
        except ValueError:
            return None

    def raise_for_status(self, allow_redirects=True):
        """Raises stored :class:`HTTPError` or :class:`URLError`, if one occurred."""

        if self.error:
            raise HTTPError(self.error)

        if (self.status_code >= 300) and (self.status_code < 400) and not allow_redirects:
            http_error = HTTPError('%s Redirection' % (self.status_code))
            http_error.response = self
            raise http_error

        elif (self.status_code >= 400) and (self.status_code < 500):
            http_error = HTTPError('%s Client Error' % (self.status_code))
            http_error.response = self
            raise http_error

        elif (self.status_code >= 500) and (self.status_code < 600):
            http_error = HTTPError('%s Server Error' % (self.status_code))
            http_error.response = self
            raise http_error

def rebuild_response(r):
    response = Response()
    response.status_code = r.get('status_code', 599)
    response.url = r.get('url', '')
    response.headers = CaseInsensitiveDict(r.get('headers', {}))
    response.content = r.get('content', '')
    response.cookies = r.get('cookies', {})
    response.error = r.get('error')
    response.time = r.get('time', 0)
    response.orig_url = r.get('orig_url', response.url)
    return response
