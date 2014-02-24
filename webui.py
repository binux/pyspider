#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-02-22 23:19:11

from webui.app import app

from fetcher import tornado_fetcher
fetcher = tornado_fetcher.Fetcher(None, None, async=False)
config = {
        'fetch': fetcher.fetch,
        }

if __name__ == '__main__':
    app.config.update(**config)
    app.debug = True
    app.run()
