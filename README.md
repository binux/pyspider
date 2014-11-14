pyspider [![Build Status](https://travis-ci.org/binux/pyspider.png?branch=master)](https://travis-ci.org/binux/pyspider) [![Coverage Status](https://coveralls.io/repos/binux/pyspider/badge.png)](https://coveralls.io/r/binux/pyspider)
========

A Powerful Spider System in Python. [Try It Now!](http://demo.pyspider.org/)

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

* python2.6/2.7
* `pip install --allow-all-external -r requirements.txt`
* `./run.py` , visit [http://localhost:5000/](http://localhost:5000/)

if ubuntu: `apt-get install python python-dev python-distribute python-pip libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml`

or [Run with Docker](https://github.com/binux/pyspider/wiki/Run-pyspider-with-Docker)

Documents
=========

* [Wiki](https://github.com/binux/pyspider/wiki)
* [Quickstart](https://github.com/binux/pyspider/wiki/Quickstart)
* [脚本编写指南](https://github.com/binux/pyspider/wiki/%E8%84%9A%E6%9C%AC%E7%BC%96%E5%86%99%E6%8C%87%E5%8D%97)
* [架构设计](http://blog.binux.me/2014/02/pyspider-architecture/)

Contribute
==========

* Use It, Open [Issue](https://github.com/binux/pyspider/issues), PR is welcome.
* [Discuss](https://github.com/binux/pyspider/issues?labels=discussion&state=open) [Document](https://github.com/binux/pyspider/wiki)


License
=======
Licensed under the Apache License, Version 2.0
