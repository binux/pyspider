Quickstart
==========

Installation
------------

* python 2.6,2.7,3.3,3.4
* `pip install --allow-all-external -r requirements.txt`
* `./run.py` , visit [http://localhost:5000/](http://localhost:5000/)

if you are using ubuntu, try:
```
apt-get install python python-dev python-distribute python-pip libcurl4-openssl-dev libxml2-dev libxslt1-dev python-lxml
```
to install binary packages first.

[Full Deployment](Deployment)

Your First Script
-----------------

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

* `def on_start(self)` is where your spider start. It will been called when you press the `run` button on dashboard.
* [`self.crawl(url, callback=self.index_page)`](self.crawl) is the most important API here. It add a new task to crawl, and the `response` will been parsed by the function `index_page`.
* `def index_page(self, response)` now get [`response`](Response). `response.doc` is a [pyquery](https://pythonhosted.org/pyquery/) object that you can locate the elements by a jquery-like API.
* `def detail_page(self, response)` return a `dict` as it's result. It will captured by a result collector called result_worker. You can override `on_result(self, result)` method to deal with results by yourself.

You can run your script step by step by green `run` button. Try it!

* `@every(minutes=24*60, seconds=0)` is a helper to tell the scheduler that this method should been called every 24*60 minutes = 1 day
* `@config(age=10*24*60*60)` is a helper to tell pages parsed by `index_page` callback should considered as expired after age. This params can also set via [`self.crawl(age=10*24*60*60)`](apis/self.crawl/#schedule)
* [API Reference](apis)

Start Running
-------------

Now save your script. It is very important, so I repeat. SAVE YOUR SCRIPT first.

1. Back to dashboard find your project.
2. Make sure the `status` is `DEBUG` or `RUNNING`.
3. Make sure `rate/burst` is not 0.
4. Press the `run` button.

![index demo](imgs/index_page.png)

Your script is running now!
