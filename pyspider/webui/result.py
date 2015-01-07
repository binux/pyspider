#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2014-10-19 16:23:55

from __future__ import unicode_literals

import six
import csv
import itertools
from io import StringIO, BytesIO

from six import iteritems
from flask import render_template, request, json
from flask import Response
from .app import app


def result_formater(results):
    common_fields = None
    for result in results:
        if isinstance(result['result'], dict):
            if common_fields is None:
                common_fields = set(result['result'].keys())
            else:
                common_fields &= set(result['result'].keys())
        else:
            common_fields = set()
    for result in results:
        result['result_formated'] = {}
        if not common_fields:
            result['others'] = result['result']
        elif not isinstance(result['result'], dict):
            result['others'] = result['result']
        else:
            result_formated = {}
            others = {}
            for key, value in iteritems(result['result']):
                if key in common_fields:
                    result_formated[key] = value
                else:
                    others[key] = value
            result['result_formated'] = result_formated
            result['others'] = others
    return common_fields or [], results


@app.route('/results')
def result():
    resultdb = app.config['resultdb']
    project = request.args.get('project')
    offset = int(request.args.get('offset', 0))
    limit = int(request.args.get('limit', 20))

    count = resultdb.count(project)
    results = list(resultdb.select(project, offset=offset, limit=limit))

    return render_template(
        "result.html", count=count, results=results, result_formater=result_formater,
        project=project, offset=offset, limit=limit, json=json
    )


@app.route('/results/dump/<project>.<_format>')
def dump_result(project, _format):
    resultdb = app.config['resultdb']
    # force update project list
    resultdb.get(project, 'any')
    if project not in resultdb.projects:
        return "no such project.", 404

    if _format == 'json':
        valid = request.args.get('style', 'rows') == 'full'
        def generator():
            first = True
            if valid:
                yield '['

            for result in resultdb.select(project):
                if valid:
                    if first:
                        first = False
                    else:
                        yield ', '

                yield json.dumps(result, ensure_ascii=False) + '\n'

            if valid:
                yield ']'

        return Response(generator(), mimetype='application/json')
    elif _format == 'txt':
        def generator():
            for result in resultdb.select(project):
                yield (
                    result['url'] + '\t' +
                    json.dumps(result['result'], ensure_ascii=False) + '\n'
                )
        return Response(generator(), mimetype='text/plain')
    elif _format == 'csv':
        def toString(obj):
            if isinstance(obj, six.binary_type):
                if six.PY2:
                    return obj
                else:
                    return obj.decode('utf8')
            elif isinstance(obj, six.text_type):
                if six.PY2:
                    return obj.encode('utf8')
                else:
                    return obj
            else:
                if six.PY2:
                    return json.dumps(obj, ensure_ascii=False).encode('utf8')
                else:
                    return json.dumps(obj, ensure_ascii=False)

        def generator():
            # python2 needs byes when python3 needs unicode
            if six.PY2:
                stringio = BytesIO()
            else:
                stringio = StringIO()
            csv_writer = csv.writer(stringio)

            it = iter(resultdb.select(project))
            first_30 = []
            for result in it:
                first_30.append(result)
                if len(first_30) >= 30:
                    break
            common_fields, _ = result_formater(first_30)
            common_fields_l = sorted(common_fields)

            csv_writer.writerow([toString('url')]
                                + [toString(x) for x in common_fields_l]
                                + [toString('...')])
            for result in itertools.chain(first_30, it):
                other = {}
                for k, v in iteritems(result['result']):
                    if k not in common_fields:
                        other[k] = v
                csv_writer.writerow(
                    [toString(result['url'])]
                    + [toString(result['result'].get(k, '')) for k in common_fields_l]
                    + [toString(other)]
                )
                yield stringio.getvalue()
                stringio.truncate(0); stringio.seek(0)
        return Response(generator(), mimetype='text/csv')
