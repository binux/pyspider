#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2014-11-24 22:27:45


import sys
from setuptools import setup, find_packages
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

import pyspider

install_requires = [
    'Flask==0.10',
    'Jinja2==2.7',
    'chardet==3.0.4',
    'cssselect==0.9',
    "lxml==4.3.3",
    'pycurl==7.43.0.3',
    'requests==2.24.0',
    'Flask-Login==0.2.11',
    'u-msgpack-python==1.6',
    'click==3.3',
    'six==1.10.0',
    'tblib==1.4.0',
    'wsgidav==2.3.0',
    'tornado>=3.2,<=4.5.3',
    'pyquery',
]

extras_require_all = [
    'mysql-connector-python==8.0.16',
    'pymongo==3.9.0',
    'redis==2.10.6',
    'redis-py-cluster==1.3.6',
    'psycopg2==2.8.2',
    'elasticsearch==2.3.0',
    'kombu==4.4.0',
    'amqp==2.4.0',
    'SQLAlchemy==1.3.10',
    'pika==1.1.0'
]

setup(
    name='pyspider',
    version=pyspider.__version__,

    description='A Powerful Spider System in Python',
    long_description=long_description,

    url='https://github.com/binux/pyspider',

    author='Roy Binux',
    author_email='roy@binux.me',

    license='Apache License, Version 2.0',

    classifiers=[
        'Development Status :: 4 - Beta',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',

        'License :: OSI Approved :: Apache Software License',

        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Environment :: Web Environment',

        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],

    keywords='scrapy crawler spider webui',

    packages=find_packages(exclude=['data', 'tests*']),

    install_requires=install_requires,

    extras_require={
        'all': extras_require_all,
        'test': [
            'coverage',
            'Werkzeug==0.16.1',
            'httpbin==0.7.0',
            'pyproxy==0.1.6',
            'easywebdav==1.2.0',
        ]
    },

    package_data={
        'pyspider': [
            'logging.conf',
            'fetcher/phantomjs_fetcher.js',
            'fetcher/splash_fetcher.lua',
            'webui/static/*.js',
            'webui/static/*.css',
            'webui/templates/*'
        ],
    },

    entry_points={
        'console_scripts': [
            'pyspider=pyspider.run:main'
        ]
    },

    test_suite='tests.all_suite',
)
