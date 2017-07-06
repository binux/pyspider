pyspider [![Build Status]][Travis CI] [![Coverage Status]][Coverage] [![Try]][Demo]
========

A Powerful Spider(Web Crawler) System in Python. **[TRY IT NOW!][Demo]**

- Write script in Python
- Powerful WebUI with script editor, task monitor, project manager and result viewer
- [MySQL](https://www.mysql.com/), [MongoDB](https://www.mongodb.org/), [Redis](http://redis.io/), [SQLite](https://www.sqlite.org/), [Elasticsearch](https://www.elastic.co/products/elasticsearch); [PostgreSQL](http://www.postgresql.org/) with [SQLAlchemy](http://www.sqlalchemy.org/) as database backend
- [RabbitMQ](http://www.rabbitmq.com/), [Beanstalk](http://kr.github.com/beanstalkd/), [Redis](http://redis.io/) and [Kombu](http://kombu.readthedocs.org/) as message queue
- Task priority, retry, periodical, recrawl by age, etc...
- Distributed architecture, Crawl Javascript pages, Python 2.{6,7}, 3.{3,4,5,6} support, etc...

Tutorial: [http://docs.pyspider.org/en/latest/tutorial/](http://docs.pyspider.org/en/latest/tutorial/)  
Documentation: [http://docs.pyspider.org/](http://docs.pyspider.org/)  
Release notes: [https://github.com/binux/pyspider/releases](https://github.com/binux/pyspider/releases)  

Sample Code 
-----------

```python
from pyspider.libs.base_handler import *


class Handler(BaseHandler):
    crawl_config = {
    }

    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://scrapy.org/', callback=self.index_page)

    @config(age=10 * 24 * 60 * 60)
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            self.crawl(each.attr.href, callback=self.detail_page)

    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('title').text(),
        }
```

[![Demo][Demo Img]][Demo]


Installation
------------

* `pip install pyspider`
* run command `pyspider`, visit [http://localhost:5000/](http://localhost:5000/)

**WARNING:** WebUI is open to the public by default, it can be used to execute any command which may harm your system. Please use it in an internal network or [enable `need-auth` for webui](http://docs.pyspider.org/en/latest/Command-Line/#-config).

Quickstart: [http://docs.pyspider.org/en/latest/Quickstart/](http://docs.pyspider.org/en/latest/Quickstart/)

Contribute
----------

* Use It
* Open [Issue], send PR
* [User Group]
* [中文问答](http://segmentfault.com/t/pyspider)


TODO
----

### v0.4.0

- [ ] a visual scraping interface like [portia](https://github.com/scrapinghub/portia)


License
-------
Licensed under the Apache License, Version 2.0


[Build Status]:         https://img.shields.io/travis/binux/pyspider/master.svg?style=flat
[Travis CI]:            https://travis-ci.org/binux/pyspider
[Coverage Status]:      https://img.shields.io/coveralls/binux/pyspider.svg?branch=master&style=flat
[Coverage]:             https://coveralls.io/r/binux/pyspider
[Try]:                  https://img.shields.io/badge/try-pyspider-blue.svg?style=flat
[Demo]:                 http://demo.pyspider.org/
[Demo Img]:             https://github.com/binux/pyspider/blob/master/docs/imgs/demo.png
[Issue]:                https://github.com/binux/pyspider/issues
[User Group]:           https://groups.google.com/group/pyspider-users
