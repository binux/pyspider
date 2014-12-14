#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-09 14:39:57

import mimetypes
from urllib import urlencode
from urlparse import urlparse, urlunparse

import six
from six import iteritems

def get_content_type(filename):
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


def _encode_params(data):
    """Encode parameters in a piece of data.

    Will successfully encode parameters when passed as a dict or a list of
    2-tuples. Order is retained if data is a list of 2-tuples but abritrary
    if parameters are supplied as a dict.
    """

    if isinstance(data, six.string_types):
        return data
    elif hasattr(data, 'read'):
        return data
    elif hasattr(data, '__iter__'):
        result = []
        for k, vs in iteritems(data):
            for v in isinstance(vs, list) and vs or [vs]:
                if v is not None:
                    result.append(
                        (k.encode('utf-8') if isinstance(k, six.text_type) else k,
                         v.encode('utf-8') if isinstance(v, six.text_type) else v))
        return urlencode(result, doseq=True)
    else:
        return data


def _utf8(key):
    if not isinstance(key, six.string_types):
        key = str(key)
    return key.encode('utf-8') if isinstance(key, six.text_type) else key


def _encode_multipart_formdata(fields, files):
    """
    fields is a sequence of (name, value) elements for regular form fields.
    files is a sequence of (name, filename, value) elements for data to be uploaded as files
    Return (content_type, body) ready for httplib.HTTP instance
    """
    BOUNDARY = b'----------ThIs_Is_tHe_bouNdaRY_$'
    CRLF = b'\r\n'
    L = []
    for key, value in iteritems(fields):
        L.append(b'--' + BOUNDARY)
        L.append(b'Content-Disposition: form-data; name="%s"' % _utf8(key))
        L.append(b'')
        L.append(_utf8(value))
    for key, (filename, value) in iteritems(files):
        L.append(b'--' + BOUNDARY)
        L.append(
            b'Content-Disposition: form-data; name="%s"; filename="%s"'
            % (_utf8(key), _utf8(filename))
        )
        L.append('Content-Type: %s' % get_content_type(filename))
        L.append('')
        L.append(value.read() if hasattr(value, "read") else _utf8(value))
    L.append('--' + BOUNDARY + '--')
    L.append('')
    body = CRLF.join(L)
    content_type = 'multipart/form-data; boundary=%s' % BOUNDARY
    return content_type, body


def _build_url(url, _params):
    """Build the actual URL to use."""

    # Support for unicode domain names and paths.
    scheme, netloc, path, params, query, fragment = urlparse(url)
    netloc = netloc.encode('idna').decode('utf-8')
    if not path:
        path = '/'

    if isinstance(scheme, six.text_type):
        scheme = scheme.encode('utf-8')
    if isinstance(netloc, six.text_type):
        netloc = netloc.encode('utf-8')
    if isinstance(path, six.text_type):
        path = path.encode('utf-8')
    if isinstance(params, six.text_type):
        params = params.encode('utf-8')
    if isinstance(query, six.text_type):
        query = query.encode('utf-8')
    if isinstance(fragment, six.text_type):
        fragment = fragment.encode('utf-8')

    enc_params = _encode_params(_params)
    if enc_params:
        if query:
            query = '%s&%s' % (query, enc_params)
        else:
            query = enc_params
    url = (urlunparse([scheme, netloc, path, params, query, fragment]))
    return url


def quote_chinese(url, encodeing="utf-8"):
    if isinstance(url, six.text_type):
        return quote_chinese(url.encode("utf-8"))
    res = [b if ord(b) < 128 else '%%%02X' % (ord(b)) for b in url]
    return "".join(res)
