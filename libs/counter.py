#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-14 17:09:50

import time
import cPickle
import logging
from collections import deque
from UserDict import DictMixin

class BaseCounter(object): pass

class AverageWindowCounter(BaseCounter):
    def __init__(self, window_size=300):
        self.window_size = window_size
        self.values = deque(maxlen=window_size)
        self.times = deque(maxlen=window_size)

    def event(self, value=1):
        self.values.append(value)
        self.times.append(time.time())

    @property
    def avg(self):
        return float(self.sum) / len(self.values)

    @property
    def sum(self):
        return sum(self.values)

    def empty(self):
        if not self.values and not self.cache_start:
            return True

class TimebaseAverageWindowCounter(BaseCounter):
    def __init__(self, window_size=30, window_interval=10):
        self.max_window_size = window_size
        self.window_size = 0
        self.window_interval = window_interval
        self.values = deque(maxlen=window_size)
        self.times = deque(maxlen=window_size)

        self.cache_value = 0
        self.cache_start = None
        self._first_data_time = None

    def event(self, value=1):
        now = time.time()
        if self._first_data_time is None:
            self._first_data_time = now

        if self.cache_start is None:
            self.cache_value = value
            self.cache_start = now
        elif now - self.cache_start > self.window_interval:
            self.values.append(self.cache_value)
            self.times.append(self.cache_start)
            self.on_append(self.cache_value, self.cache_start)
            self.cache_value = value
            self.cache_start = now
        else:
            self.cache_value += value

    def _trim_window(self):
        now = time.time()
        if self.cache_start and now - self.cache_start > self.window_interval:
            self.values.append(self.cache_value)
            self.times.append(self.cache_start)
            self.on_append(self.cache_value, self.cache_start)
            self.cache_value = 0
            self.cache_start = None

        if self.window_size != self.max_window_size and self._first_data_time is not None:
            time_passed = now - self._first_data_time
            self.window_size = min(self.max_window_size, time_passed / self.window_interval)
        window_limit = now - self.window_size * self.window_interval
        while self.times and self.times[0] < window_limit:
            self.times.popleft()
            self.values.popleft()

    @property
    def avg(self):
        if not self.window_size:
            return 0
        return float(self.sum) / self.window_size / self.window_interval

    @property
    def sum(self):
        self._trim_window()
        return sum(self.values)

    def empty(self):
        self._trim_window()
        if not self.values and not self.cache_start:
            return True

    def on_append(self, value, time):
        pass

class CounterValue(DictMixin):
    def __init__(self, manager, keys):
        self.manager = manager
        self._keys = keys

    def __getitem__(self, key):
        if key == '__value__':
            key = self._keys
            return self.manager.counters[key]
        else:
            key = self._keys + (key, )

        available_keys = []
        for _key in self.manager.counters:
            if _key[:len(key)] == key:
                available_keys.append(_key)

        if len(available_keys) == 0:
            raise KeyError
        elif len(available_keys) == 1:
            if available_keys[0] == key:
                return self.manager.counters[key]
            else:
                return CounterValue(self.manager, key)
        else:
            return CounterValue(self.manager, key)

    def keys(self):
        result = set()
        for key in self.manager.counters:
            if key[:len(self._keys)] == self._keys:
                key = key[len(self._keys):]
                result.add(key[0] if key else '__value__')
        return result

    def to_dict(self, get_value=None):
        result = {}
        for key, value in self.iteritems():
            if isinstance(value, BaseCounter):
                if get_value is not None:
                    value = getattr(value, get_value)
                result[key] = value
            else:
                result[key] = value.to_dict(get_value)
        return result

class CounterManager(DictMixin):
    def __init__(self, cls=TimebaseAverageWindowCounter):
        self.cls = cls
        self.counters = {}

    def event(self, key, value=1):
        if isinstance(key, basestring):
            key = (key, )
        assert isinstance(key, tuple), "event key type error"
        if key not in self.counters:
            self.counters[key] = self.cls()
        self.counters[key].event(value)

    def trim(self):
        for key, value in self.counters.items():
            if value.empty():
                del self.counters[key]

    def __getitem__(self, key):
        key = (key, )
        available_keys = []
        for _key in self.counters:
            if _key[:len(key)] == key:
                available_keys.append(_key)

        if len(available_keys) == 0:
            raise KeyError
        elif len(available_keys) == 1:
            if available_keys[0] == key:
                return self.counters[key]
            else:
                return CounterValue(self, key)
        else:
            return CounterValue(self, key)

    def keys(self):
        result = set()
        for key in self.counters:
            result.add(key[0] if key else ())
        return result

    def to_dict(self, get_value=None):
        self.trim()
        result = {}
        for key, value in self.iteritems():
            if isinstance(value, BaseCounter):
                if get_value is not None:
                    value = getattr(value, get_value)
                result[key] = value
            else:
                result[key] = value.to_dict(get_value)
        return result

    def dump(self, filename):
        try:
            cPickle.dump(self.counters, open(filename, 'wb'))
        except:
            logging.exception("can't dump counter to file: %s" % filename)
            return False
        return True

    def load(self, filename):
        try:
            self.counters = cPickle.load(open(filename))
        except:
            logging.exception("can't load counter from file: %s" % filename)
            return False
        return True
