self.crawl
===========

self.crawl(url, **kwargs)
-------------------------

`self.crawl` is the main interface to tell pyspider which url(s) should be crawled.

### Parameters:

* `url` - the url or url list to be crawled. <a name="url" href="#url">¶</a>
* `callback` - the method to parse the response. _default: `__call__` _  <a name="callback" href="#callback">¶</a>

```python
def on_start(self):
    self.crawl('http://scrapy.org/', callback=self.index_page)
```

the following parameters are optional

* `age` - the period of validity of the task. The page would be regarded as not modified during the period. _default: 0(never recrawl)_ <a name="age" href="#age">¶</a>

```python
@config(age=10 * 24 * 60 * 60)
def index_page(self, response):
    ...
```
> Every pages parsed by the callback `index_page` would be regarded not changed within 10 days. If you submit the task within 10 days since last crawled it would be discarded.

* `priority` - the priority of task to be scheduled, higher the better. _default: 0_ <a name="priority" href="#priority">¶</a>

```python
def index_page(self):
    self.crawl('http://www.example.org/page2.html', callback=self.index_page)
    self.crawl('http://www.example.org/233.html', callback=self.detail_page,
               priority=1)
```
> The page `233.html` would be crawled before `page2.html`. Use this parameter can do a [BFS](http://en.wikipedia.org/wiki/Breadth-first_search) and reduce the number of tasks in queue(which may cost more memory resources).

* `exetime` - the executed time of task in unix timestamp. _default: 0(immediately)_ <a name="exetime" href="#exetime">¶</a>

```python
import time
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.callback,
               exetime=time.time()+30*60)
```
> The page would be crawled 30 minutes later.

* `retries` - retry times while failed. _default: 3_ <a name="retries" href="#retries">¶</a>
* `itag` - a marker from frontier page to reveal the potential modification of the task. It will be compared to its last value, recrawl when it's changed. _default: None_ <a name="itag" href="#itag">¶</a>

```python
def index_page(self, response):
    for item in response.doc('.item').items():
        self.crawl(item.find('a').attr.url, callback=self.detail_page,
                   itag=item.find('.update-time').text())
```
> In the sample, `.update-time` is used as itag. If it's not changed, the request would be discarded.

Or you can use `itag` with `Handler.crawl_config` to specify the script version if you want to restart all of the tasks.

```python
class Handler(BaseHandler):
    crawl_config = {
        'itag': 'v223'
    }
```
> Change the value of itag after you modified the script and click run button again. It don't matter if not set before. 

* `auto_recrawl` - when enabled, task would be recrawled every `age` time. _default: False_ <a name="auto_recrawl" href="#auto_recrawl">¶</a>

```python
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.callback,
               age=5*60*60, auto_recrawl=True)
```
> The page would be restarted every `age` 5 hours.

* `method` - HTTP method to use. _default: GET_ <a name="method" href="#method">¶</a>
* `params` - dictionary of URL parameters to append to the URL. <a name="params" href="#params">¶</a>

```python
def on_start(self):
    self.crawl('http://httpbin.org/get', callback=self.callback,
               params={'a': 123, 'b': 'c'})
    self.crawl('http://httpbin.org/get?a=123&b=c', callback=self.callback)
```
> The two requests are the same.

* `data` - the body to attach to the request. If a dictionary is provided, form-encoding will take place. <a name="data" href="#data">¶</a>

```python
def on_start(self):
    self.crawl('http://httpbin.org/post', callback=self.callback,
               method='POST', data={'a': 123, 'b': 'c'})
```

* `files` - dictionary of `{field: {filename: 'content'}}` files to multipart upload.` <a name="files" href="#files">¶</a>
* `headers` - dictionary of headers to send. <a name="headers" href="#headers">¶</a>
* `cookies` - dictionary of cookies to attach to this request. <a name="cookies" href="#cookies">¶</a>
* `timeout` - maximum time in seconds to fetch the page. _default: 120_ <a name="timeout" href="#timeout">¶</a>
* `allow_redirects` - follow `30x` redirect _default: True_ <a name="allow_redirects" href="#allow_redirects">¶</a>
* `proxy` - proxy server of `username:password@hostname:port` to use, only http proxy is supported currently. <a name="proxy" href="#proxy">¶</a>

```python
class Handler(BaseHandler):
    crawl_config = {
        'proxy': 'localhost:8080'
    }
```
> `Handler.crawl_config` can be used with `proxy` to set a proxy for whole project.

* `etag` - use HTTP Etag mechanism to pass the process if the content of the page is not changed. _default: True_ <a name="etag" href="#etag">¶</a>
* `last_modifed` - use HTTP Last-Modified header mechanism to pass the process if the content of the page is not changed. _default: True_ <a name="last_modifed" href="#last_modifed">¶</a>
* `fetch_type` - set to `js` to enable JavaScript fetcher. _default: None_ <a name="fetch_type" href="#fetch_type">¶</a>
* `js_script` - JavaScript run before or after page loaded, should been wrapped by a function like `function() { document.write("binux"); }`. <a name="js_script" href="#js_script">¶</a>


```python
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.callback,
               fetch_type='js', js_script='''
               function() {
                   window.scrollTo(0,document.body.scrollHeight);
                   return 123;
               }
               ''')
```
> The script would scroll the page to bottom. The value returned in function could be captured via `Response.js_script_result`.

* `js_run_at` - run JavaScript specified via `js_script` at `document-start` or `document-end`. _default: `document-end`_ <a name="js_run_at" href="#js_run_at">¶</a>

* `js_viewport_width/js_viewport_height` - set the size of the viewport for the JavaScript fetcher of the layout process. <a name="js_viewport_width"><a name="js_viewport_height" href="#js_viewport_height">¶</a></a>

* `load_images` - load images when JavaScript fetcher enabled. _default: False_ <a name="load_images" href="#load_images">¶</a>

* `save` - a object pass to the callback method, can be visit via `response.save`. <a name="save" href="#save">¶</a>


```python
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.callback,
               save={'a': 123})

def callback(self, response):
    return response.save['a']
```
> `123` would be returned in `callback`

* `taskid` - unique id to identify the task, default is the MD5 check code of the URL, can be overridden by method `def get_taskid(self, task)` <a name="taskid" href="#taskid">¶</a>

```python
import son
from pyspider.libs.utils import md5string
def get_taskid(self, task):
    return md5string(task['url']+json.dumps(task['data']))
```
> Only url is md5 -ed as taskid by default, the code above add `data` of POST request as part of taskid.

* `force_update` - force update task params even if the task is in `ACTIVE` status. <a name="force_update" href="#force_update">¶</a>

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
    self.crawl('http://www.example.org/list-1.html', callback=self.index_page)
    self.crawl('http://www.example.org/product-233', callback=self.detail_page)
    
@config(age=10*24*60*60)
def detail_page(self, response):
    return {...}
```

`age` of `list-1.html` is 15min while the `age` of `product-233.html` is 10days. Because the callback of `product-233.html` is `detail_page`, means it's a `detail_page` so it shares the config of `detail_page`.

Handler.crawl_config = {}
-------------------------
default parameters of `self.crawl` for the whole project. 

```python
class Handler(BaseHandler):
    crawl_config = {
        'headers': {
            'User-Agent': 'GoogleBot',
        }
    }
    
    ...
```
> crawl_config set a project level user-agent.

