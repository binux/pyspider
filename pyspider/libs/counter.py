#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-14 17:09:50

from __future__ import unicode_literals, division, absolute_import

import time
import logging
from collections import deque
try:
    from UserDict import DictMixin
except ImportError:
    from collections import Mapping as DictMixin

import six
from six import iteritems
from six.moves import cPickle


class BaseCounter(object):

    def __init__(self):
        raise NotImplementedError

    def event(self, value=1):
        """Fire a event."""
        raise NotImplementedError

    def value(self, value):
        """Set counter value."""
        raise NotImplementedError

    @property
    def avg(self):
        """Get average value"""
        raise NotImplementedError

    @property
    def sum(self):
        """Get sum of counter"""
        raise NotImplementedError

    def empty(self):
        """Clear counter"""
        raise NotImplementedError


class TotalCounter(BaseCounter):
    """Total counter"""

    def __init__(self):
        self.cnt = 0

    def event(self, value=1):
        self.cnt += value

    def value(self, value):
        self.cnt = value

    @property
    def avg(self):
        return self.cnt

    @property
    def sum(self):
        return self.cnt

    def empty(self):
        return self.cnt == 0


class AverageWindowCounter(BaseCounter):
    """
    Record last N(window) value
    """

    def __init__(self, window_size=300):
        self.window_size = window_size
        self.values = deque(maxlen=window_size)

    def event(self, value=1):
        self.values.append(value)

    value = event

    @property
    def avg(self):
        return self.sum / len(self.values)

    @property
    def sum(self):
        return sum(self.values)

    def empty(self):
        if not self.values:
            return True


class TimebaseAverageEventCounter(BaseCounter):
    """
    Record last window_size * window_interval seconds event.

    records will trim ever window_interval seconds
    """

    def __init__(self, window_size=30, window_interval=10):
        self.max_window_size = window_size
        self.window_size = 0
        self.window_interval = window_interval
        self.values = deque(maxlen=window_size)
        self.events = deque(maxlen=window_size)
        self.times = deque(maxlen=window_size)

        self.cache_value = 0
        self.cache_event = 0
        self.cache_start = None
        self._first_data_time = None

    def event(self, value=1):
        now = time.time()
        if self._first_data_time is None:
            self._first_data_time = now

        if self.cache_start is None:
            self.cache_value = value
            self.cache_event = 1
            self.cache_start = now
        elif now - self.cache_start > self.window_interval:
            self.values.append(self.cache_value)
            self.events.append(self.cache_event)
            self.times.append(self.cache_start)
            self.on_append(self.cache_value, self.cache_start)
            self.cache_value = value
            self.cache_event = 1
            self.cache_start = now
        else:
            self.cache_value += value
            self.cache_event += 1
        return self

    def value(self, value):
        self.cache_value = value

    def _trim_window(self):
        now = time.time()
        if self.cache_start and now - self.cache_start > self.window_interval:
            self.values.append(self.cache_value)
            self.events.append(self.cache_event)
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
            self.events.popleft()
            self.values.popleft()

    @property
    def avg(self):
        events = (sum(self.events) + self.cache_event)
        if not events:
            return 0
        return float(self.sum) / events

    @property
    def sum(self):
        self._trim_window()
        return sum(self.values) + self.cache_value

    def empty(self):
        self._trim_window()
        if not self.values and not self.cache_start:
            return True

    def on_append(self, value, time):
        pass


class TimebaseAverageWindowCounter(BaseCounter):
    """
    Record last window_size * window_interval seconds values.

    records will trim ever window_interval seconds
    """

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
        return self

    def value(self, value):
        self.cache_value = value

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
        sum = float(self.sum)
        if not self.window_size:
            return 0
        return sum / self.window_size / self.window_interval

    @property
    def sum(self):
        self._trim_window()
        return sum(self.values) + self.cache_value

    def empty(self):
        self._trim_window()
        if not self.values and not self.cache_start:
            return True

    def on_append(self, value, time):
        pass


class CounterValue(DictMixin):
    """
    A dict like value item for CounterManager.
    """

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
        for _key in self.manager.counters.keys():
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

    def __len__(self):
        return len(self.keys())

    def __iter__(self):
        return iter(self.keys())

    def __contains__(self, key):
        return key in self.keys()

    def keys(self):
        result = set()
        for key in self.manager.counters.keys():
            if key[:len(self._keys)] == self._keys:
                key = key[len(self._keys):]
                result.add(key[0] if key else '__value__')
        return result

    def to_dict(self, get_value=None):
        """Dump counters as a dict"""
        result = {}
        for key, value in iteritems(self):
            if isinstance(value, BaseCounter):
                if get_value is not None:
                    value = getattr(value, get_value)
                result[key] = value
            else:
                result[key] = value.to_dict(get_value)
        return result


class CounterManager(DictMixin):
    """
    A dict like counter manager.

    When using a tuple as event key, say: ('foo', 'bar'), You can visite counter
    with manager['foo']['bar'].  Or get all counters which first element is 'foo'
    by manager['foo'].

    It's useful for a group of counters.
    """

    def __init__(self, cls=TimebaseAverageWindowCounter):
        """init manager with Counter cls"""
        self.cls = cls
        self.counters = {}

    def event(self, key, value=1):
        """Fire a event of a counter by counter key"""
        if isinstance(key, six.string_types):
            key = (key, )
        assert isinstance(key, tuple), "event key type error"
        if key not in self.counters:
            self.counters[key] = self.cls()
        self.counters[key].event(value)
        return self

    def value(self, key, value=1):
        """Set value of a counter by counter key"""
        if isinstance(key, six.string_types):
            key = (key, )
        assert isinstance(key, tuple), "event key type error"
        if key not in self.counters:
            self.counters[key] = self.cls()
        self.counters[key].value(value)
        return self

    def trim(self):
        """Clear not used counters"""
        for key, value in list(iteritems(self.counters)):
            if value.empty():
                del self.counters[key]

    def __getitem__(self, key):
        key = (key, )
        available_keys = []
        for _key in self.counters.keys():
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

    def __delitem__(self, key):
        key = (key, )
        available_keys = []
        for _key in self.counters.keys():
            if _key[:len(key)] == key:
                available_keys.append(_key)
        for _key in available_keys:
            del self.counters[_key]

    def __iter__(self):
        return iter(self.keys())

    def __len__(self):
        return len(self.keys())

    def keys(self):
        result = set()
        for key in self.counters.keys():
            result.add(key[0] if key else ())
        return result

    def to_dict(self, get_value=None):
        """Dump counters as a dict"""
        self.trim()
        result = {}
        for key, value in iteritems(self):
            if isinstance(value, BaseCounter):
                if get_value is not None:
                    value = getattr(value, get_value)
                result[key] = value
            else:
                result[key] = value.to_dict(get_value)
        return result

    def dump(self, filename):
        """Dump counters to file"""
        try:
            with open(filename, 'wb') as fp:
                cPickle.dump(self.counters, fp)
        except Exception as e:
            logging.warning("can't dump counter to file %s: %s", filename, e)
            return False
        return True

    def load(self, filename):
        """Load counters to file"""
        try:
            with open(filename) as fp:
                self.counters = cPickle.load(fp)
        except:
            logging.debug("can't load counter from file: %s", filename)
            return False
        return True
