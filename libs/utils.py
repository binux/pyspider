#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-06 11:50:13

import logging
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

def hide_me(tb, g=globals()):
    base_tb = tb
    try:
        while tb and tb.tb_frame.f_globals is not g:
            tb = tb.tb_next
        while tb and tb.tb_frame.f_globals is g:
            tb = tb.tb_next
    except Exception, e:
        logging.exception(e)
        tb = base_tb
    if not tb:
        tb = base_tb
    return tb
