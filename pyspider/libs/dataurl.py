#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-16 10:33:20

import six
from base64 import b64encode, b64decode
from . import utils
from six.moves.urllib.parse import quote, unquote


def encode(data, mime_type='', charset='utf-8', base64=True):
    """
    Encode data to DataURL
    """
    if isinstance(data, six.text_type):
        data = data.encode(charset)
    else:
        charset = None
    if base64:
        data = utils.text(b64encode(data))
    else:
        data = utils.text(quote(data))

    result = ['data:', ]
    if mime_type:
        result.append(mime_type)
    if charset:
        result.append(';charset=')
        result.append(charset)
    if base64:
        result.append(';base64')
    result.append(',')
    result.append(data)

    return ''.join(result)


def decode(data_url):
    """
    Decode DataURL data
    """
    metadata, data = data_url.rsplit(',', 1)
    _, metadata = metadata.split('data:', 1)
    parts = metadata.split(';')
    if parts[-1] == 'base64':
        data = b64decode(data)
    else:
        data = unquote(data)

    for part in parts:
        if part.startswith("charset="):
            data = data.decode(part[8:])
    return data
