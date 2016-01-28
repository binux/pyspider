#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-03-27 20:12:11

import six
import csv
import json
import itertools
from io import StringIO, BytesIO
from six import iteritems


def result_formater(results):
    common_fields = None
    for result in results:
        result.setdefault('result', None)
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
    return common_fields or set(), results


def dump_as_json(results, valid=False):
    first = True
    if valid:
        yield '['

    for result in results:
        if valid:
            if first:
                first = False
            else:
                yield ', '

        yield json.dumps(result, ensure_ascii=False) + '\n'

    if valid:
        yield ']'


def dump_as_txt(results):
    for result in results:
        yield (
            result.get('url', None) + '\t' +
            json.dumps(result.get('result', None), ensure_ascii=False) + '\n'
        )


def dump_as_csv(results):
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

    # python2 needs byes when python3 needs unicode
    if six.PY2:
        stringio = BytesIO()
    else:
        stringio = StringIO()
    csv_writer = csv.writer(stringio)

    it = iter(results)
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
        csv_writer.writerow(
            [toString(result['url'])]
            + [toString(result['result_formated'].get(k, '')) for k in common_fields_l]
            + [toString(result['others'])]
        )
        yield stringio.getvalue()
        stringio.truncate(0)
        stringio.seek(0)
