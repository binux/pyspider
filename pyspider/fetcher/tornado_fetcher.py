#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-12-17 11:07:19

from __future__ import unicode_literals

import six
import copy
import time
import json
import logging
import threading
import tornado.ioloop
import tornado.httputil
import tornado.httpclient
import pyspider

from six.moves import queue, http_cookies
from requests import cookies
from six.moves.urllib.parse import urljoin, urlsplit
from tornado.curl_httpclient import CurlAsyncHTTPClient
from tornado.simple_httpclient import SimpleAsyncHTTPClient
from pyspider.libs import utils, dataurl, counter
from .cookie_utils import extract_cookies_to_jar
logger = logging.getLogger('fetcher')


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
    user_agent = "pyspider/%s (+http://pyspider.org/)" % pyspider.__version__
    default_options = {
        'method': 'GET',
        'headers': {
        },
        'use_gzip': True,
        'timeout': 120,
    }
    phantomjs_proxy = None

    def __init__(self, inqueue, outqueue, poolsize=100, proxy=None, async=True):
        self.inqueue = inqueue
        self.outqueue = outqueue

        self.poolsize = poolsize
        self._running = False
        self._quit = False
        self.proxy = proxy
        self.async = async
        self.ioloop = tornado.ioloop.IOLoop()

        # binding io_loop to http_client here
        if self.async:
            self.http_client = MyCurlAsyncHTTPClient(max_clients=self.poolsize,
                                                     io_loop=self.ioloop)
        else:
            self.http_client = tornado.httpclient.HTTPClient(
                MyCurlAsyncHTTPClient, max_clients=self.poolsize
            )

        self._cnt = {
            '5m': counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(30, 10)),
            '1h': counter.CounterManager(
                lambda: counter.TimebaseAverageWindowCounter(60, 60)),
        }

    def send_result(self, type, task, result):
        '''Send fetch result to processor'''
        if self.outqueue:
            try:
                self.outqueue.put((task, result))
            except Exception as e:
                logger.exception(e)

    def fetch(self, task, callback=None):
        '''Do one fetch'''
        url = task.get('url', 'data:,')
        if callback is None:
            callback = self.send_result
        if url.startswith('data:'):
            return self.data_fetch(url, task, callback)
        elif task.get('fetch', {}).get('fetch_type') in ('js', 'phantomjs'):
            return self.phantomjs_fetch(url, task, callback)
        else:
            return self.http_fetch(url, task, callback)

    def sync_fetch(self, task):
        '''Synchronization fetch'''
        wait_result = threading.Condition()
        _result = {}

        def callback(type, task, result):
            wait_result.acquire()
            _result['type'] = type
            _result['task'] = task
            _result['result'] = result
            wait_result.notify()
            wait_result.release()

        wait_result.acquire()
        self.fetch(task, callback=callback)
        while 'result' not in _result:
            wait_result.wait()
        wait_result.release()
        return _result['result']

    def data_fetch(self, url, task, callback):
        '''A fake fetcher for dataurl'''
        self.on_fetch('data', task)
        result = {}
        result['orig_url'] = url
        result['content'] = dataurl.decode(url)
        result['headers'] = {}
        result['status_code'] = 200
        result['url'] = url
        result['cookies'] = {}
        result['time'] = 0
        result['save'] = task.get('fetch', {}).get('save')
        if len(result['content']) < 70:
            logger.info("[200] %s 0s", url)
        else:
            logger.info(
                "[200] data:,%s...[content:%d] 0s",
                result['content'][:70],
                len(result['content'])
            )

        callback('data', task, result)
        self.on_result('data', task, result)
        return task, result

    def handle_error(self, type, url, task, start_time, callback, error):
        result = {
            'status_code': getattr(error, 'code', 599),
            'error': utils.text(error),
            'content': "",
            'time': time.time() - start_time,
            'orig_url': url,
            'url': url,
        }
        logger.error("[%d] %s, %r %.2fs",
                     result['status_code'], url, error, result['time'])
        callback(type, task, result)
        self.on_result(type, task, result)
        return task, result

    allowed_options = ['method', 'data', 'timeout', 'cookies']

    def http_fetch(self, url, task, callback):
        '''HTTP fetcher'''
        start_time = time.time()

        self.on_fetch('http', task)
        fetch = copy.deepcopy(self.default_options)
        fetch['url'] = url
        fetch['headers']['User-Agent'] = self.user_agent
        task_fetch = task.get('fetch', {})
        for each in self.allowed_options:
            if each in task_fetch:
                fetch[each] = task_fetch[each]
        fetch['headers'].update(task_fetch.get('headers', {}))

        if task.get('track'):
            track_headers = tornado.httputil.HTTPHeaders(
                task.get('track', {}).get('fetch', {}).get('headers') or {})
            track_ok = task.get('track', {}).get('process', {}).get('ok', False)
        else:
            track_headers = {}
            track_ok = False
        # proxy
        proxy_string = None
        if isinstance(task_fetch.get('proxy'), six.string_types):
            proxy_string = task_fetch['proxy']
        elif self.proxy and task_fetch.get('proxy', True):
            proxy_string = self.proxy
        if proxy_string:
            if '://' not in proxy_string:
                proxy_string = 'http://' + proxy_string
            proxy_splited = urlsplit(proxy_string)
            if proxy_splited.username:
                fetch['proxy_username'] = proxy_splited.username
            if proxy_splited.password:
                fetch['proxy_password'] = proxy_splited.password
            fetch['proxy_host'] = proxy_splited.hostname
            fetch['proxy_port'] = proxy_splited.port or 8080

        # etag
        if task_fetch.get('etag', True):
            _t = None
            if isinstance(task_fetch.get('etag'), six.string_types):
                _t = task_fetch.get('etag')
            elif track_ok:
                _t = track_headers.get('etag')
            if _t:
                fetch['headers'].setdefault('If-None-Match', _t)
        # last modifed
        if task_fetch.get('last_modified', True):
            _t = None
            if isinstance(task_fetch.get('last_modifed'), six.string_types):
                _t = task_fetch.get('last_modifed')
            elif track_ok:
                _t = track_headers.get('last-modified')
            if _t:
                fetch['headers'].setdefault('If-Modified-Since', _t)

        session = cookies.RequestsCookieJar()

        # fix for tornado request obj
        fetch['headers'] = tornado.httputil.HTTPHeaders(fetch['headers'])
        if 'Cookie' in fetch['headers']:
            c = http_cookies.SimpleCookie()
            c.load(fetch['headers']['Cookie'])
            for key in c:
                session.set(key, c[key])
            del fetch['headers']['Cookie']
        fetch['follow_redirects'] = False
        if 'timeout' in fetch:
            fetch['connect_timeout'] = fetch['request_timeout'] = fetch['timeout']
            del fetch['timeout']
        if 'data' in fetch:
            fetch['body'] = fetch['data']
            del fetch['data']
        if 'cookies' in fetch:
            session.update(fetch['cookies'])
            del fetch['cookies']

        store = {}
        store['max_redirects'] = task_fetch.get('max_redirects', 5)

        def handle_response(response):
            extract_cookies_to_jar(session, response.request, response.headers)
            if (response.code in (301, 302, 303, 307)
                    and response.headers.get('Location')
                    and task_fetch.get('allow_redirects', True)):
                if store['max_redirects'] <= 0:
                    error = tornado.httpclient.HTTPError(
                        599, 'Maximum (%d) redirects followed' % task_fetch.get('max_redirects', 5),
                        response)
                    return handle_error(error)
                if response.code in (302, 303):
                    fetch['method'] = 'GET'
                    if 'body' in fetch:
                        del fetch['body']
                fetch['url'] = urljoin(fetch['url'], response.headers['Location'])
                fetch['request_timeout'] -= time.time() - start_time
                if fetch['request_timeout'] < 0:
                    fetch['request_timeout'] = 0.1
                fetch['connect_timeout'] = fetch['request_timeout']
                store['max_redirects'] -= 1
                return make_request(fetch)

            result = {}
            result['orig_url'] = url
            result['content'] = response.body or ''
            result['headers'] = dict(response.headers)
            result['status_code'] = response.code
            result['url'] = response.effective_url or url
            result['cookies'] = session.get_dict()
            result['time'] = time.time() - start_time
            result['save'] = task_fetch.get('save')
            if response.error:
                result['error'] = utils.text(response.error)
            if 200 <= response.code < 300:
                logger.info("[%d] %s %.2fs", response.code, url, result['time'])
            else:
                logger.warning("[%d] %s %.2fs", response.code, url, result['time'])
            callback('http', task, result)
            self.on_result('http', task, result)
            return task, result

        handle_error = lambda x: self.handle_error('http',
                                                   url, task, start_time, callback, x)

        def make_request(fetch):
            try:
                request = tornado.httpclient.HTTPRequest(**fetch)
                cookie_header = cookies.get_cookie_header(session, request)
                if cookie_header:
                    request.headers['Cookie'] = cookie_header
                if self.async:
                    self.http_client.fetch(request, handle_response)
                else:
                    return handle_response(self.http_client.fetch(request))
            except tornado.httpclient.HTTPError as e:
                if e.response:
                    return handle_response(e.response)
                else:
                    return handle_error(e)
            except Exception as e:
                logger.exception(fetch)
                return handle_error(e)

        return make_request(fetch)

    phantomjs_adding_options = ['js_run_at', 'js_script', 'load_images']

    def phantomjs_fetch(self, url, task, callback):
        '''Fetch with phantomjs proxy'''
        start_time = time.time()

        self.on_fetch('phantomjs', task)
        if not self.phantomjs_proxy:
            result = {
                "orig_url": url,
                "content": "phantomjs is not enabled.",
                "headers": {},
                "status_code": 501,
                "url": url,
                "cookies": {},
                "time": 0,
                "save": task.get('fetch', {}).get('save')
            }
            logger.warning("[501] %s 0s", url)
            callback('http', task, result)
            self.on_result('http', task, result)
            return task, result

        request_conf = {
            'follow_redirects': False
        }

        fetch = copy.deepcopy(self.default_options)
        fetch['url'] = url
        fetch['headers']['User-Agent'] = self.user_agent
        task_fetch = task.get('fetch', {})
        for each in task_fetch:
            if each != 'headers':
                fetch[each] = task_fetch[each]
        fetch['headers'].update(task_fetch.get('headers', {}))

        if 'timeout' in fetch:
            request_conf['connect_timeout'] = fetch['timeout']
            request_conf['request_timeout'] = fetch['timeout'] + 1

        session = cookies.RequestsCookieJar()
        request = tornado.httpclient.HTTPRequest(url=fetch['url'])
        if fetch.get('cookies'):
            session.update(fetch['cookies'])
            if 'Cookie' in request.headers:
                del request.headers['Cookie']
            fetch['headers']['Cookie'] = cookies.get_cookie_header(session, request)

        def handle_response(response):
            if not response.body:
                return handle_error(Exception('no response from phantomjs'))

            try:
                result = json.loads(utils.text(response.body))
                if response.error:
                    result['error'] = utils.text(response.error)
            except Exception as e:
                return handle_error(e)

            if result.get('status_code', 200):
                logger.info("[%d] %s %.2fs", result['status_code'], url, result['time'])
            else:
                logger.error("[%d] %s, %r %.2fs", result['status_code'],
                             url, result['content'], result['time'])
            callback('phantomjs', task, result)
            self.on_result('phantomjs', task, result)
            return task, result

        handle_error = lambda x: self.handle_error('phantomjs',
                                                   url, task, start_time, callback, x)

        try:
            request = tornado.httpclient.HTTPRequest(
                url="%s" % self.phantomjs_proxy, method="POST",
                body=json.dumps(fetch), **request_conf)
            if self.async:
                self.http_client.fetch(request, handle_response)
            else:
                return handle_response(self.http_client.fetch(request))
        except tornado.httpclient.HTTPError as e:
            if e.response:
                return handle_response(e.response)
            else:
                return handle_error(e)
        except Exception as e:
            return handle_error(e)

    def run(self):
        '''Run loop'''
        logger.info("fetcher starting...")

        def queue_loop():
            if not self.outqueue or not self.inqueue:
                return
            while not self._quit:
                try:
                    if self.outqueue.full():
                        break
                    if self.http_client.free_size() <= 0:
                        break
                    task = self.inqueue.get_nowait()
                    # FIXME: decode unicode_obj should used after data selete from
                    # database, it's used here for performance
                    task = utils.decode_unicode_obj(task)
                    self.fetch(task)
                except queue.Empty:
                    break
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    logger.exception(e)
                    break

        tornado.ioloop.PeriodicCallback(queue_loop, 100, io_loop=self.ioloop).start()
        self._running = True

        try:
            self.ioloop.start()
        except KeyboardInterrupt:
            pass

        logger.info("fetcher exiting...")

    def quit(self):
        '''Quit fetcher'''
        self._running = False
        self._quit = True
        self.ioloop.stop()

    def size(self):
        return self.http_client.size()

    def xmlrpc_run(self, port=24444, bind='127.0.0.1', logRequests=False):
        '''Run xmlrpc server'''
        import umsgpack
        try:
            from xmlrpc.server import SimpleXMLRPCServer
            from xmlrpc.client import Binary
        except ImportError:
            from SimpleXMLRPCServer import SimpleXMLRPCServer
            from xmlrpclib import Binary

        server = SimpleXMLRPCServer((bind, port), allow_none=True, logRequests=logRequests)
        server.register_introspection_functions()
        server.register_multicall_functions()

        server.register_function(self.quit, '_quit')
        server.register_function(self.size)

        def sync_fetch(task):
            result = self.sync_fetch(task)
            result = Binary(umsgpack.packb(result))
            return result
        server.register_function(sync_fetch, 'fetch')

        def dump_counter(_time, _type):
            return self._cnt[_time].to_dict(_type)
        server.register_function(dump_counter, 'counter')

        server.timeout = 0.5
        while not self._quit:
            server.handle_request()
        server.server_close()

    def on_fetch(self, type, task):
        '''Called before task fetch'''
        pass

    def on_result(self, type, task, result):
        '''Called after task fetched'''
        status_code = result.get('status_code', 599)
        if status_code != 599:
            status_code = (int(status_code) / 100 * 100)
        self._cnt['5m'].event((task.get('project'), status_code), +1)
        self._cnt['1h'].event((task.get('project'), status_code), +1)

        if type == 'http' and result.get('time'):
            content_len = len(result.get('content', ''))
            self._cnt['5m'].event((task.get('project'), 'speed'),
                                  float(content_len) / result.get('time'))
            self._cnt['1h'].event((task.get('project'), 'speed'),
                                  float(content_len) / result.get('time'))
            self._cnt['5m'].event((task.get('project'), 'time'), result.get('time'))
            self._cnt['1h'].event((task.get('project'), 'time'), result.get('time'))
