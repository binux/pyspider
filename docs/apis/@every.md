@every(minutes=0, seconds=0)
============================

method will been called every `minutes` or `seconds`


```python
@every(minutes=24 * 60)
def on_start(self):
    for url in urllist:
        self.crawl(url, callback=self.index_page)
```

The urls would be restarted every 24 hours. Note that, if `age` is also used and the period is longer then `@every`, the crawl request would be discarded as it's regarded as not changed:

```python
@every(minutes=24 * 60)
def on_start(self):
    self.crawl('http://www.example.org/', callback=self.index_page)

@config(age=10 * 24 * 60 * 60)
def index_page(self):
    ...
```

> Even though the crawl request triggered every day, but it's discard and only restarted every 10 days.

