self.crawl
===========

self.crawl(url, **kwargs)
-------------------------

`self.crawl` is the main interface to tell which url will be followed.

###basis

* `url` - the url to been followed. Can be a list of urls.
* `callback` - which method should parse the response. A callback is needed in most case. _default: `__call__` _

### schedule
* `age` - re-crawl if `last_crawl_time + age < now`.  
> **NOTE: tasks will not restart automatically.** `age` is something like: hey, spider I found this link, don't restart it if you had seen it in `age` seconds, it may not changed.

* `priority` - higher the better
* `exetime`
* `retries`
* `itag` - compare to its last value, re-crawl when it's changed.
* `auto_recrawl` - when enabled, task would be recrawled every `age` time.

### fetch
* `method`
* `params` - query string, like `?a=b`
* `data` - post body, `str` or `dict`
* `files` - `{'filename': ('file.name': 'content')}`
* `headers` - `dict`
* `cookies` - `dict`
* `timeout` - in seconds
* `allow_redirects` - follow `30x` redirect _default: True_
* `proxy`
* `etag` - enable etag _default: True_
* `last_modifed` - enable last modifed _default: True_

#### enable JavaScript fetcher (need support by fetcher)
* `fetch_type` - set to `js` to enable JavaScript fetcher
* `js_script` - JavaScript run before or after page loaded, should been wrapped by a function like `function() { document.write("binux"); }`
* `js_run_at` - `document-start` or `document-end` _default: `document-end`_
* `load_images` - _default: False_

### process
* `save` - anything json-able object pass to next response. _can been got from `response.save`_

### other
* `taskid` - unique id for each task. _default: md5(url)_ , can be overrided by define your own `def get_taskid(self, task)`
* `force_update` - force update task params when task is in `ACTIVE` status.

cURL command
------------

`self.crawl(curl_command)`

cURL is a command line tool to make a HTTP request. cURL command can get from chrome devtools > network panel, right click a request and `Copy as cURL`.

You can use cURL command as the first argument of `self.crawl`. It will parse the command and make the HTTP request just like curl do.

@config(**kwargs)
-----------------
default kwargs for self.crawl of method. Any `self.crawl` with this callback will use this config.

Handler.crawl_config = {}
-------------------------
default config for the project. 
