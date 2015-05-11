self.crawl
===========

self.crawl(url, **kwargs)
-------------------------

`self.crawl` is the main interface to tell pyspider which url(s) should be crawled.

### Parameters:

* `url` - the url or url list to be crawled.
* `callback` - the method to parse the response. _default: `__call__` _  

the following parameters are optional

* `age` - the term of validity of the task. The page would be regarded as not modified during the term. _default: 0(never recrawl)_
* `priority` - the priority of task to be scheduled, higher the better. _default: 0_
* `exetime` - the executed time of task in unix timestamp. _default: 0(immediately)_
* `retries` - retry times while failed. _default: 3_
* `itag` - a marker from frontier page to reveal the potential modification of the task. It will be compared to its last value, recrawl when it's changed. _default: None_
* `auto_recrawl` - when enabled, task would be recrawled every `age` time. _default: False_
* `method` - HTTP method to use. _default: GET_
* `params` - dictionary of URL parameters to append to the URL.
* `data` - the body to attach to the request. If a dictionary is provided, form-encoding will take place.
* `files` - dictionary of `{field: {filename: 'content'}}` files to multipart upload.`
* `headers` - dictionary of headers to send.
* `cookies` - dictionary of cookies to attach to this request.
* `timeout` - maximum time in seconds to fetch the page. _default: 120_
* `allow_redirects` - follow `30x` redirect _default: True_
* `proxy` - proxy server of `username:password@hostname:port` to use, only http proxy is supported currently.
* `etag` - use HTTP Etag mechanism to pass the process if the content of the page is not changed. _default: True_
* `last_modifed` - use HTTP Last-Modified header mechanism to pass the process if the content of the page is not changed. _default: True_
* `fetch_type` - set to `js` to enable JavaScript fetcher. _default: None_
* `js_script` - JavaScript run before or after page loaded, should been wrapped by a function like `function() { document.write("binux"); }`.
* `js_run_at` - run JavaScript specified via `js_script` at `document-start` or `document-end`. _default: `document-end`_
* `js_viewport_width/js_viewport_height` - set the size of the viewport for the JavaScript fetcher of the layout process.
* `load_images` - load images when JavaScript fetcher enabled. _default: False_
* `save` - a object pass to the callback method, can be visit via `response.save`.
* `taskid` - unique id to identify the task, default is the MD5 sum code of the URL, can be overridden by method `def get_taskid(self, task)`
* `force_update` - force update task params even if the task is in `ACTIVE` status.

cURL command
------------

`self.crawl(curl_command)`

cURL is a command line tool to make a HTTP request. It can easily get form Chrome Devtools > Network panel,  right click the request and "Copy as cURL".

You can use cURL command as the first argument of `self.crawl`. It will parse the command and make the HTTP request just like curl do.

@config(**kwargs)
-----------------
default parameters of `self.crawl` when use the decorated method as callback. For example:

```python
@config(age=15*60)
def index_page(self, response):
    self.crawl('http://www.example.org/list-1', callback=self.index_page)
    self.crawl('http://www.example.org/product-233', callback=self.detail_page)
    
@config(age=10*24*60*60)
def detail_page(self, response):
    return {...}
```

`age` of 'http://www.example.org/list-1' is 15min while the `age` of 'http://www.example.org/product-233' is 10days. Because the callback of 'http://www.example.org/product-233' is `detail_page`, means it's a `detail_page` so it shares the config of `detail_page`.

Handler.crawl_config = {}
-------------------------
default parameters of `self.crawl` for the whole project. 


