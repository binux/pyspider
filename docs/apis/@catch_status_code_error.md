@catch_status_code_error
========================

non-200 response will been regarded as fetch failed and will not pass to callback. use this decorator to override this feature.

```python
def on_start(self):
    self.crawl('http://httpbin.org/status/404', self.callback)

@catch_status_code_error  
def callback(self, response):
    ...
```

>  The `callback` would not be executed as the request is failed (with status code 404). With the `@catch_status_code_error` decorater, the `callback` would be executed even if the request failed.

