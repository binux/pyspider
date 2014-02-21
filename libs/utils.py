#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-06 11:50:13

import hashlib

md5string = lambda x: hashlib.md5(x).hexdigest()

class ReadOnlyDict(dict):
    def __setitem__(self, key, value):
        raise "dict is read-only"

def getitem(obj, key=0, default=None):
    try:
        return obj[key]
    except:
        return default
