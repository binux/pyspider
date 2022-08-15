#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-10-12 22:17:57

from __future__ import unicode_literals, division

import six
import csv
import time
import json
import unittest
from six import StringIO

from pyspider.libs import result_dump

results1 = [
    {'taskid': 'taskid1', 'url': 'http://example.org/url1', 'pdatetime': time.time(),
     'result': {'a': 1, 'b': 2} },
    {'taskid': 'taskid1', 'url': 'http://example.org/url1', 'pdatetime': time.time(),
     'result': {'a': 1, 'b': 2, 'c': 3} },
]

results2 = results1 + [
    {'taskid': 'taskid1', 'url': 'http://example.org/url1', 'pdatetime': time.time(),
     'result': [1, 2, '中文', u'中文'] },
]

results_error = results2 + [
    {'taskid': 'taskid1', 'url': 'http://example.org/url1', 'pdatetime': time.time(),
     'result': None},
    {'taskid': 'taskid1', 'url': 'http://example.org/url1', 'pdatetime': time.time() },
    {'taskid': 'taskid1', 'pdatetime': time.time() },
]

result_list_error = [
    {'taskid': 'taskid1', 'url': 'http://example.org/url1', 'pdatetime': time.time(),
     'result': [{"rate": "8.2", "title": '1'}, {"rate": "8.2", "title": '1'}]},
    {'taskid': 'taskid1', 'url': 'http://example.org/url1', 'pdatetime': time.time(),
     'result': [{"rate": "8.2", "title": '1'}, {"rate": "8.2", "title": '1'}]},
]

class TestResultDump(unittest.TestCase):
    def test_result_formater_1(self):
        common_fields, results = result_dump.result_formater(results1)
        self.assertEqual(common_fields, set(('a', 'b')))

    def test_result_formater_2(self):
        common_fields, results = result_dump.result_formater(results2)
        self.assertEqual(common_fields, set())

    def test_result_formater_error(self):
        common_fields, results = result_dump.result_formater(results_error)
        self.assertEqual(common_fields, set())

    def test_dump_as_json(self):
        for i, line in enumerate((''.join(
                result_dump.dump_as_json(results2))).splitlines()):
            self.assertDictEqual(results2[i], json.loads(line))

    def test_dump_as_json_valid(self):
        ret = json.loads(''.join(result_dump.dump_as_json(results2, True)))
        for i, j in zip(results2, ret):
            self.assertDictEqual(i, j)

    def test_dump_as_txt(self):
        for i, line in enumerate((''.join(
                result_dump.dump_as_txt(results2))).splitlines()):
            url, json_data = line.split('\t', 2)
            self.assertEqual(results2[i]['result'], json.loads(json_data))

    def test_dump_as_csv(self):
        reader = csv.reader(StringIO(''.join(result_dump.dump_as_csv(results1))))
        for row in reader:
            self.assertEqual(len(row), 4)

    def test_dump_as_csv_case_1(self):
        reader = csv.reader(StringIO(''.join(result_dump.dump_as_csv(result_list_error))))
        for row in reader:
            self.assertEqual(len(row), 2)
