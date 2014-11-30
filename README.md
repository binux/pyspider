pyspider [![Build Status](https://img.shields.io/travis/binux/pyspider/master.svg?style=flat)](https://travis-ci.org/binux/pyspider) [![Coverage Status](https://img.shields.io/coveralls/binux/pyspider.svg?branch=master&style=flat)](https://coveralls.io/r/binux/pyspider)
========

A Powerful Spider(Web Crawler) System in Python. [Try It Now!](http://demo.pyspider.org/)

- Write script in python with powerful API
- Powerful WebUI with script editor, task monitor, project manager and result viewer
- MySQL, MongoDB, SQLite as database backend 
- Javascript pages supported!
- Task priority, retry, periodical and recrawl by age or marks in index page (like update time)
- Distributed architecture


Sample Code:

```python
from libs.base_handler import *

class Handler(BaseHandler):
    '''
    this is a sample handler
    '''
    @every(minutes=24*60, seconds=0)
    def on_start(self):
        self.crawl('http://scrapy.org/', callback=self.index_page)

    @config(age=10*24*60*60)
    def index_page(self, response):
        for each in response.doc('a[href^="http://"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    def detail_page(self, response):
        return {
                "url": response.url,
                "title": response.doc('title').text(),
                }
```

[![demo](http://ww1.sinaimg.cn/large/7d46d69fjw1emavy6e9gij21kw0uldvy.jpg)](http://demo.pyspider.org/)


Installation
============

* python2.6/7 (windows is not supported currently)
* `pip install --allow-all-external -r requirements.txt`
* `./run.py` , visit [http://localhost:5000/](http://localhost:5000/)

if ubuntu: `apt-get install python python-dev python-distribute python-pip libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml`

[Running with Docker](https://github.com/binux/pyspider/wiki/Running-pyspider-with-Docker)


Documents
=========

* [Quickstart](https://github.com/binux/pyspider/wiki/Quickstart)
* [API Reference](https://github.com/binux/pyspider/wiki/API-Reference)
* more documents: [Wiki](https://github.com/binux/pyspider/wiki)


Contribute
==========

* Use It, Open [Issue](https://github.com/binux/pyspider/issues), PR is welcome.
* [User Group](https://groups.google.com/group/pyspider-users)


License
=======
Licensed under the Apache License, Version 2.0
