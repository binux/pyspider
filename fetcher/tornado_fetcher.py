#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-12-17 11:07:19

import time
import Queue
import logging
import cookie_utils
import tornado.ioloop
import tornado.httputil
import tornado.httpclient
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.simple_httpclient import SimpleAsyncHTTPClient
from libs import dataurl, counter

class MyCurlAsyncHTTPClient(CurlAsyncHTTPClient):
    def free_size(self):
        return len(self._free_list)
    def size(self):
        return len(self._curls) - self.free_size()

class MySimpleAsyncHTTPClient(SimpleAsyncHTTPClient):
    def free_size(self):
        return self.max_clients - self.size()
    def size(self):
        return len(self.active)

fetcher_output = {
        "status_code": int,
        "orig_url": str,
        "url": str,
        "headers": dict,
        "content": str,
        "cookies": dict,
        }

class Fetcher(object):
    user_agent = "BaiDuSpider"
    default_options = {
            'method': 'GET',
            'headers': {},
            'timeout': 120,
            }
    allowed_options = ['method', 'headers', 'data', 'timeout', 'allow_redirects', 'cookies', ]

    def __init__(self, inqueue, outqueue, poolsize=10, proxy=None, async=True):
        self.inqueue = inqueue
        self.outqueue = outqueue

        self.poolsize = poolsize
        self._pause = False
        self._quit = False
        self.proxy = proxy
        self.async = async
        
        if async:
            self.http_client = MyCurlAsyncHTTPClient(max_clients=self.poolsize)
        else:
            self.http_client = tornado.httpclient.HTTPClient(MyCurlAsyncHTTPClient, max_clients=self.poolsize)

        self._init()
        
    def fetch(self, task, callback=None):
        url = task.get('url', 'data:,')
        if callback is None:
            callback = self.put_result
        if url.startswith('data:'):
            return self.data_fetch(url, task, callback)
        else:
            return self.http_fetch(url, task, callback)

    def data_fetch(self, url, task, callback):
        self.on_fetch('data', task)
        result = {}
        result['orig_url'] = url
        result['content'] = dataurl.decode(url)
        result['status_code'] = 200
        result['url'] = url
        result['time'] = 0
        if len(result['content']) < 70:
            logging.info("[200] %s 0s" % url)
        else:
            logging.info("[200] data:,%s...[content:%d] 0s" % (result['content'][:70], len(result['content'])))

        callback('data', task, result)
        self.on_result('data', task, result)
        return task, result

    def http_fetch(self, url, task, callback):
        self.on_fetch('http', task)
        fetch = dict(self.default_options)
        fetch.setdefault('url', url)
        fetch.setdefault('headers', {})
        fetch.setdefault('allow_redirects', True)
        fetch.setdefault('use_gzip', True)
        fetch['headers'].setdefault('User-Agent', self.user_agent)
        task_fetch = task.get('fetch', {})
        for each in self.allowed_options:
            if each in task_fetch:
                fetch[each] = task_fetch[each]

        track_headers = task.get('track', {}).get('fetch', {}).get('headers', {})
        #proxy
        if self.proxy and task_fetch.get('proxy', True):
            fetch['proxy_host'] = self.proxy['http'].split(":")[0]
            fetch['proxy_port'] = int(self.proxy['http'].split(":")[1])
        #etag
        if task_fetch.get('etag', True):
            _t = task_fetch.get('etag') if isinstance(task_fetch.get('etag'), basestring) \
                                          else track_headers.get('etag')
            if _t:
                fetch['headers'].setdefault('If-None-Match', _t)
        #last modifed
        if task_fetch.get('last_modified', True):
            _t = task_fetch.get('last_modifed') \
                        if isinstance(task_fetch.get('last_modifed'), basestring) \
                        else track_headers.get('last-modified')
            if _t:
                fetch['headers'].setdefault('If-Modifed-Since', _t)

        #fix for tornado request obj
        cookie = None
        if 'allow_redirects' in fetch:
            fetch['follow_redirects'] = fetch['allow_redirects']
            del fetch['allow_redirects']
        if 'timeout' in fetch:
            fetch['connect_timeout'] = fetch['timeout']
            fetch['request_timeout'] = fetch['timeout']
            del fetch['timeout']
        if 'data' in fetch:
            fetch['body'] = fetch['data']
            del fetch['data']
        if 'cookies' in fetch:
            cookie = fetch['cookies']
            del fetch['cookies']

        def handle_response(response):
            response.headers = final_headers
            session.extract_cookies_to_jar(request, cookie_headers)
            if response.error and not isinstance(response.error, tornado.httpclient.HTTPError):
                result = {'status_code': 599, 'error': "%r" % response.error,
                          'time': time.time() - start_time, 'orig_url': url, 'url': url, }
                callback('http', task, result)
                self.on_result('http', task, result)
                return task, result
            result = {}
            result['orig_url'] = url
            result['content'] = response.body or ''
            result['headers'] = dict(response.headers)
            result['status_code'] = response.code
            result['url'] = response.effective_url or url
            result['cookies'] = session.to_dict()
            result['time'] = time.time() - start_time
            if 200 <= response.code < 300:
                logging.info("[%d] %s %.2fs" % (response.code, url, result['time']))
            else:
                logging.warning("[%d] %s %.2fs" % (response.code, url, result['time']))
            callback('http', task, result)
            self.on_result('http', task, result)
            return task, result

        def header_callback(line):
            line = line.strip()
            if line.startswith("HTTP/"):
                final_headers.clear()
                return
            if not line:
                return
            final_headers.parse_line(line)
            cookie_headers.parse_line(line)

        start_time = time.time()
        session = cookie_utils.CookieSession()
        cookie_headers = tornado.httputil.HTTPHeaders()
        final_headers = tornado.httputil.HTTPHeaders()
        try:
            request = tornado.httpclient.HTTPRequest(header_callback=header_callback, **fetch)
            if cookie:
                session.update(cookie)
                request.headers.add('Cookie', self.session.get_cookie_header(request))
            if self.async:
                response = self.http_client.fetch(request, handle_response)
            else:
                return handle_response(self.http_client.fetch(request))
        except Exception, e:
            result = {'status_code': 599, 'error': "%r" % e, 'time': time.time() - start_time,
                      'orig_url': url, 'url': url, }
            logging.error("[599] %s, %r %.2fs" % (url, e, result['time']))
            callback('http', task, result)
            self.on_result('http', task, result)
            return task, result

    def run(self):
        while not self._quit:
            try:
                if self.outqueue.full():
                    time.sleep(1)
                    continue

                task = self.inqueue.get()
                self.fetch(task)
            except Queue.Empty:
                time.sleep(1)
                continue
            except Exception, e:
                logging.exception(e)
                time.sleep(30)
                continue

    def size(self):
        return self.http_client.size()

    def quit(self):
        self._quit = True

    def xmlrpc_run(self, port, bind='127.0.0.1'):
        from SimpleXMLRPCServer import SimpleXMLRPCServer

        server = SimpleXMLRPCServer((bind, port), allow_none=True)
        server.register_introspection_functions()
        server.register_multicall_functions()

        server.register_function(self.size)
        server.register_function(self.unpause)
        server.register_function(self.quit, '_quit')
        server.register_function(lambda : self._5min_counter.to_dict('avg'), 'dump_5min')
        server.register_function(lambda : self._http_time.to_dict('avg'), 'dump_avgtime')

        server.serve_forever()

    def _init(self):
        self._5min_counter = counter.CounterManager(
                lambda : counter.TimebaseAverageWindowCounter(60, 5))
        self._http_time = counter.CounterManager(
                lambda : counter.AverageWindowCounter(300))

    def on_fetch(self, type, task):
        """type in ('data', 'http')"""
        self._5min_counter.event((task.get('project'), 'fetch'))
        self._5min_counter.event(('__all__', 'fetch'))

    def put_result(self, type, task, result):
        """type in ('data', 'http')"""
        if self.outqueue:
            try:
                self.outqueue.put((task, result))
            except Exception, e:
                logging.exception(e)

    def on_result(self, type, task, result):
        """type in ('data', 'http')"""
        status_code = result.get('status_code', 599)
        if status_code != 599:
            status_code = (int(status_code) / 100 * 100)
        self._5min_counter.event((task.get('project'), status_code))
        self._5min_counter.event(('__all__', status_code))
        
        content_len = len(result.get('content', ''))
        self._5min_counter.event((task.get('project'), 'speed'), content_len)
        self._5min_counter.event(('__all__', 'speed'), content_len)

        if type == 'http':
            self._5min_counter.event((task.get('project'), 'time'), result.get('time'))
            self._5min_counter.event(('__all__', 'time'), result.get('time'))
