# -*- coding: utf-8 -*-

from six import reraise
from six.moves import builtins
from six.moves.urllib.parse import urljoin
from six import iteritems, itervalues

try:
    import flask_login as login
except ImportError:
    from flask.ext import login

try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode