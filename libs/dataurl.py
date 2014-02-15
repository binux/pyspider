#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<17175297.hk@gmail.com>
#         http://binux.me
# Created on 2012-11-16 10:33:20

from urllib import quote, unquote

def encode(data, mime_type='', charset='utf-8', base64=True):
    if isinstance(data, unicode):
        data = data.encode(charset)
    else:
        charset = None
    if base64:
        data = data.encode('base64').replace('\n', '')
    else:
        data = quote(data)

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
    metadata, data = data_url.rsplit(',', 1)
    _, metadata = metadata.split('data:', 1)
    parts = metadata.split(';')
    if parts[-1] == 'base64':
        data = data.decode("base64")
    else:
        data = unquote(data)

    for part in parts:
        if part.startswith("charset="):
            data = data.decode(part[8:])
    return data

if __name__ == '__main__':
    pass
