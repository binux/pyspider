#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-09 14:39:57

import mimetypes

import six
import shlex
from six.moves.urllib.parse import urlparse, urlunparse
from requests.models import RequestEncodingMixin


def get_content_type(filename):
    """Guessing file type by filename"""
    return mimetypes.guess_type(filename)[0] or 'application/octet-stream'


_encode_params = RequestEncodingMixin._encode_params


def _encode_multipart_formdata(fields, files):
    body, content_type = RequestEncodingMixin._encode_files(files, fields)
    return content_type, body


def _build_url(url, _params):
    """Build the actual URL to use."""

    # Support for unicode domain names and paths.
    scheme, netloc, path, params, query, fragment = urlparse(url)
    netloc = netloc.encode('idna').decode('utf-8')
    if not path:
        path = '/'

    if six.PY2:
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
    """Quote non-ascii characters"""
    if isinstance(url, six.text_type):
        return quote_chinese(url.encode(encodeing))
    if six.PY3:
        res = [six.int2byte(b).decode('latin-1') if b < 128 else '%%%02X' % b for b in url]
    else:
        res = [b if ord(b) < 128 else '%%%02X' % ord(b) for b in url]
    return "".join(res)


def curl_to_arguments(curl):
    kwargs = {}
    headers = {}
    command = None
    urls = []
    current_opt = None

    for part in shlex.split(curl):
        if command is None:
            # curl
            command = part
        elif not part.startswith('-') and not current_opt:
            # waiting for url
            urls.append(part)
        elif current_opt is None and part.startswith('-'):
            # flags
            if part == '--compressed':
                kwargs['use_gzip'] = True
            else:
                current_opt = part
        else:
            # option
            if current_opt is None:
                raise TypeError('Unknow curl argument: %s' % part)
            elif current_opt in ('-H', '--header'):
                key_value = part.split(':', 1)
                if len(key_value) == 2:
                    key, value = key_value
                    headers[key.strip()] = value.strip()
            elif current_opt in ('-d', '--data'):
                kwargs['data'] = part
            elif current_opt in ('--data-binary'):
                if part[0] == '$':
                    part = part[1:]
                kwargs['data'] = part
            elif current_opt in ('-X', '--request'):
                kwargs['method'] = part
            else:
                raise TypeError('Unknow curl option: %s' % current_opt)
            current_opt = None

    if not urls:
        raise TypeError('curl: no URL specified!')
    if current_opt:
        raise TypeError('Unknow curl option: %s' % current_opt)

    kwargs['urls'] = urls
    if headers:
        kwargs['headers'] = headers

    return kwargs
