#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-19 16:23:55

from app import app
from flask import abort, render_template, request, json

@app.route('/results')
def result():
    resultdb = app.config['resultdb']
    project = request.args.get('project')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 20))

    count = resultdb.count(project)
    results = list(resultdb.select(project, offset=offset, limit=limit))

    def result_formater(results):
        common_fields = None
        for result in results:
            if isinstance(result['result'], dict):
                if common_fields is None:
                    common_fields = set(result['result'].keys())
                else:
                    common_fields &= set(result['result'].keys())
        for result in results:
            result['result_formated'] = {}
            if not common_fields:
                result['others'] = result['result']
            elif not isinstance(result['result'], dict):
                result['others'] = result['result']
            else:
                result_formated = {}
                others = {}
                for key, value in result['result'].iteritems():
                    if key in common_fields:
                        result_formated[key] = value
                    else:
                        others[key] = value
                result['result_formated'] = result_formated
                result['others'] = others
        return common_fields or [], results

    return render_template("result.html", count=count, results=results, result_formater=result_formater,
            project=project, offset=offset, limit=limit, json=json)
