Level 3: Render with PhantomJS
==============================

Sometimes web page is too complex to find out the API request. It's time to meet the power of [PhantomJS].

To use PhantomJS, you should have PhantomJS [installed](http://phantomjs.org/download.html). If you are running pyspider with `all` mode, PhantomJS is enabled if excutable in the `PATH`.

Make sure phantomjs is working by running
```
$ pyspider phantomjs
```

Continue with the rest of the tutorial if the output is
```
Web server running on port 25555
```

Use PhantomJS
-------------

When pyspider with PhantomJS connected, you can enable this feature by adding a parameter `fetch_type='js'` to `self.crawl`. We use PhantomJS to scrape channel list of  [http://www.twitch.tv/directory/game/Dota%202](http://www.twitch.tv/directory/game/Dota%202) which is loaded with AJAX we discussed in [Level 2](tutorial/AJAX-and-more-HTTP#ajax):

```
class Handler(BaseHandler):
    def on_start(self):
        self.crawl('http://www.twitch.tv/directory/game/Dota%202',
                   fetch_type='js', callback=self.index_page)
             
    def index_page(self, response):
        return {
            "url": response.url,
            "channels": [{
                "title": x('.title').text(),
                "viewers": x('.info').contents()[2],
                "name": x('.info a').text(),
            } for x in response.doc('.stream.item').items()]
        }
```
> I used some API to handle the list of streams. You can find complete API reference from [PyQuery complete API](https://pythonhosted.org/pyquery/api.html)

Running JavaScript on Page
--------------------------

We will try to scrape images from [http://www.pinterest.com/categories/popular/](http://www.pinterest.com/categories/popular/) in this section. Only 25 images is shown at the beginning, more images would be loaded when you scroll to the bottom of the page.

To scrape images as many as posible we can use a [`js_script` parameter](/apis/self.crawl/#enable-javascript-fetcher-need-support-by-fetcher) to set some function wrapped JavaScript codes to simulate the scroll action: 

```
class Handler(BaseHandler):
    def on_start(self):
        self.crawl('http://www.pinterest.com/categories/popular/',
                   fetch_type='js', js_script="""
                   function() {
                       window.scrollTo(0,document.body.scrollHeight);
                   }
                   """, callback=self.index_page)

    def index_page(self, response):
        return {
            "url": response.url,
            "images": [{
                "title": x('.richPinGridTitle').text(),
                "img": x('.pinImg').attr('src'),
                "author": x('.creditName').text(),
            } for x in response.doc('.item').items() if x('.pinImg')]
        }
```

> * Script would been executed after page loaded(can been changed via [`js_run_at` parameter](/apis/self.crawl/#enable-javascript-fetcher-need-support-by-fetcher))
> * We scroll once after page loaded, you can scroll multiple times using [`setTimeout`](https://developer.mozilla.org/en-US/docs/Web/API/WindowTimers.setTimeout). PhantomJS will fetch as many items as possible before timeout arrived.

Online demo: [http://demo.pyspider.org/debug/tutorial_pinterest](http://demo.pyspider.org/debug/tutorial_pinterest)



[PhantomJS]:           http://phantomjs.org/
