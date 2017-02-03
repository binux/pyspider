#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-08 22:31:17

import random

from flask import Blueprint
from flask import request, render_template

from pyspider.webui._compat import urlencode


bp = Blueprint("bench_test", __name__, url_prefix="/bench")


class Item(object):
    def __init__(self, arg, name):
        self.arg = arg
        self.name = name


@bp.route('/')
def bench_test():
    args = request.args
    total = int(args.get('total', 10000))
    show = int(args.get('show', 20))
    nlist = [random.randint(1, total) for _ in range(show)]
    items = []
    args_ = dict(args)
    for nl in nlist:
        args_['n'] = nl
        argstr = urlencode(sorted(args_.items()), doseq=True)
        item = Item(argstr, nl)
        items.append(item)
    return render_template("bench_test.html", items=items)
