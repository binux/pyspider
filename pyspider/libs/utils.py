#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<i@binux.me>
#         http://binux.me
# Created on 2012-11-06 11:50:13

import logging
import hashlib
import datetime
import base64

md5string = lambda x: hashlib.md5(x).hexdigest()


class ReadOnlyDict(dict):

    def __setitem__(self, key, value):
        raise "dict is read-only"


def getitem(obj, key=0, default=None):
    try:
        return obj[key]
    except:
        return default


def hide_me(tb, g=globals()):
    base_tb = tb
    try:
        while tb and tb.tb_frame.f_globals is not g:
            tb = tb.tb_next
        while tb and tb.tb_frame.f_globals is g:
            tb = tb.tb_next
    except Exception as e:
        logging.exception(e)
        tb = base_tb
    if not tb:
        tb = base_tb
    return tb


def run_in_thread(func, *args, **kwargs):
    from threading import Thread
    thread = Thread(target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread


def run_in_subprocess(func, *args, **kwargs):
    from multiprocessing import Process
    thread = Process(target=func, args=args, kwargs=kwargs)
    thread.daemon = True
    thread.start()
    return thread


def format_date(date, gmt_offset=0, relative=True, shorter=False, full_format=False):
    """Formats the given date (which should be GMT).

    By default, we return a relative time (e.g., "2 minutes ago"). You
    can return an absolute date string with ``relative=False``.

    You can force a full format date ("July 10, 1980") with
    ``full_format=True``.

    This method is primarily intended for dates in the past.
    For dates in the future, we fall back to full format.
    """
    if not date:
        return '-'
    if isinstance(date, float) or isinstance(date, int):
        date = datetime.datetime.utcfromtimestamp(date)
    now = datetime.datetime.utcnow()
    if date > now:
        if relative and (date - now).seconds < 60:
            # Due to click skew, things are some things slightly
            # in the future. Round timestamps in the immediate
            # future down to now in relative mode.
            date = now
        else:
            # Otherwise, future dates always use the full format.
            full_format = True
    local_date = date - datetime.timedelta(minutes=gmt_offset)
    local_now = now - datetime.timedelta(minutes=gmt_offset)
    local_yesterday = local_now - datetime.timedelta(hours=24)
    difference = now - date
    seconds = difference.seconds
    days = difference.days

    format = None
    if not full_format:
        if relative and days == 0:
            if seconds < 50:
                return ("1 second ago" if seconds <= 1 else
                        "%(seconds)d seconds ago") % {"seconds": seconds}

            if seconds < 50 * 60:
                minutes = round(seconds / 60.0)
                return ("1 minute ago" if minutes <= 1 else
                        "%(minutes)d minutes ago") % {"minutes": minutes}

            hours = round(seconds / (60.0 * 60))
            return ("1 hour ago" if hours <= 1 else
                    "%(hours)d hours ago") % {"hours": hours}

        if days == 0:
            format = "%(time)s"
        elif days == 1 and local_date.day == local_yesterday.day and \
                relative:
            format = "yesterday" if shorter else "yesterday at %(time)s"
        elif days < 5:
            format = "%(weekday)s" if shorter else "%(weekday)s at %(time)s"
        elif days < 334:  # 11mo, since confusing for same month last year
            format = "%(month_name)s-%(day)s" if shorter else \
                "%(month_name)s-%(day)s at %(time)s"

    if format is None:
        format = "%(month_name)s %(day)s, %(year)s" if shorter else \
            "%(month_name)s %(day)s, %(year)s at %(time)s"

    str_time = "%d:%02d" % (local_date.hour, local_date.minute)

    return format % {
        "month_name": local_date.month - 1,
        "weekday": local_date.weekday(),
        "day": str(local_date.day),
        "year": str(local_date.year),
        "time": str_time
    }


class TimeoutError(Exception):
    pass

try:
    import signal
    if not hasattr(signal, 'SIGALRM'):
        raise ImportError('signal')

    class timeout:

        def __init__(self, seconds=1, error_message='Timeout'):
            self.seconds = seconds
            self.error_message = error_message

        def handle_timeout(self, signum, frame):
            raise TimeoutError(self.error_message)

        def __enter__(self):
            if self.seconds:
                signal.signal(signal.SIGALRM, self.handle_timeout)
                signal.alarm(self.seconds)

        def __exit__(self, type, value, traceback):
            if self.seconds:
                signal.alarm(0)
except ImportError:
    class timeout:

        def __init__(self, seconds=1, error_message='Timeout'):
            pass

        def __enter__(self):
            pass

        def __exit__(self, type, value, traceback):
            pass


def utf8(string):
    if isinstance(string, unicode):
        return string.encode('utf8')
    return string


def pretty_unicode(string):
    if isinstance(string, unicode):
        return string
    try:
        return string.decode("utf8")
    except UnicodeDecodeError:
        return string.decode('Latin-1').encode('unicode_escape')


def unicode_string(string):
    if isinstance(string, unicode):
        return string
    try:
        return string.decode("utf8")
    except UnicodeDecodeError:
        return '[BASE64-DATA]' + base64.b64encode(string) + '[/BASE64-DATA]'


def unicode_dict(_dict):
    r = {}
    for k, v in _dict.iteritems():
        r[unicode_string(k)] = unicode_obj(v)
    return r


def unicode_list(_list):
    return [unicode_obj(x) for x in _list]


def unicode_obj(obj):
    if isinstance(obj, dict):
        return unicode_dict(obj)
    elif isinstance(obj, (list, tuple)):
        return unicode_list(obj)
    elif isinstance(obj, basestring):
        return unicode_string(obj)
    elif isinstance(obj, (int, float)):
        return obj
    elif obj is None:
        return obj
    else:
        try:
            return unicode(obj)
        except:
            return unicode(repr(obj))


def decode_unicode_string(string):
    if string.startswith('[BASE64-DATA]') and string.endswith('[/BASE64-DATA]'):
        return base64.b64decode(string[len('[BASE64-DATA]'):-len('[/BASE64-DATA]')])
    return string


def decode_unicode_obj(obj):
    if isinstance(obj, dict):
        r = {}
        for k, v in obj.iteritems():
            r[decode_unicode_string(k)] = decode_unicode_obj(v)
        return r
    elif isinstance(obj, basestring):
        return decode_unicode_string(obj)
    elif isinstance(obj, (list, tuple)):
        return [decode_unicode_obj(x) for x in obj]
    else:
        return obj


class Get(object):

    def __init__(self, getter):
        self.getter = getter

    def __get__(self, instance, owner):
        return self.getter()


class ObjectDict(dict):

    def __getattr__(self, name):
        ret = self.__getitem__(name)
        if hasattr(ret, '__get__'):
            return ret.__get__(self, ObjectDict)
        return ret
