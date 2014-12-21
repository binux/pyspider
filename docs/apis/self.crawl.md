self.crawl
===========

self.crawl(url, **kwargs)
-------------------------

`self.crawl` is the main interface to tell which url will been followed.

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
* `save` - anything json-able object pass to next response. _can been get from `response.save`_

### other
* `taskid` - uniq id for each task. _default: md5(url)_ 
* `force_update` - force update task params when task is in `ACTIVE` status.

@config(**kwargs)
-----------------
default kwargs for self.crawl of method. Any `self.crawl` with this callback will use this config.

Handler.crawl_config = {}
-------------------------
default config for the project. 
