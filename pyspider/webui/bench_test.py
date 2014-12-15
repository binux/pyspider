#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-12-08 22:31:17

import random
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

from flask import request
from .app import app


@app.route('/bench')
def bench_test():
    total = int(request.args.get('total', 10000))
    show = int(request.args.get('show', 20))
    nlist = [random.randint(1, total) for _ in range(show)]
    result = []
    result.append("<html><head></head><body>")
    args = dict(request.args)
    for nl in nlist:
        args['n'] = nl
        argstr = urlencode(sorted(args.items()), doseq=True)
        result.append("<a href='/bench?{0}'>follow {1}</a><br>".format(argstr, nl))
    result.append("</body></html>")
    return "".join(result)
