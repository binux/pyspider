Level 1: HTML and CSS Selector
==============================

In this tutorial, we will scrape information of movies and TV from [IMDb].


Before Start
------------

You should have pyspider installed. You can refer to the documentation [QuickStart](QuickStart). Or test your code on [demo.pyspider.org](http://demo.pyspider.org).

Some basic knowledges you should know before scraping:

* [Web][WWW] is a system of interlinked hypertext pages.
* Pages is identified on the Web via uniform resource locator ([URL]).
* Pages transferred via the Hypertext Transfer Protocol ([HTTP]).
* Web Pages structured using HyperText Markup Language ([HTML]).

To scrape information from web is

1. Finding URLs of the pages contain the information we want.
2. Fetching the pages via HTTP.
3. Extracting the information from HTML.
4. Finding more URL contains what we want, go back to 2.


Pick a start URL
----------------

As we want to get all of the movies on [IMDb], the first thing is finding a list.  A good list page may:

* containing links to the [detail pages](http://www.imdb.com/title/tt0167260/) as many as possible
* by following next page, you can traverse all of items
* list sorted by last update time decreasing would be a great help to find latest items

By looking around on the index page of [IMDb], I found this:

![IMDb front page](imgs/tutorial_imdb_front.png)

[http://www.imdb.com/search/title?count=100&title_type=feature,tv_series,tv_movie&ref_=nv_ch_mm_1](http://www.imdb.com/search/title?count=100&title_type=feature,tv_series,tv_movie&ref_=nv_ch_mm_1)

### Creating a project

You can find "Create" button on the bottom right of baseboard. Click and name the project.

![Creating a project](imgs/creating_a_project.png)

Changing the crawl URL in `on_start` callback:

```
    @every(minutes=24 * 60)
    def on_start(self):
        self.crawl('http://www.imdb.com/search/title?count=100&title_type=feature,tv_series,tv_movie&ref_=nv_ch_mm_1', callback=self.index_page)
```

> *`self.crawl` would do everything needed to fetch the page for you and call the `callback` method to parse the response.  
> The [`@every` decorator](http://docs.pyspider.org/en/latest/apis/@every/) represents it would executed every day, make sure not missing any new movies.*

Click the green `run` button, you should find a red 1 above follows, switch to follows panel, click the green play button:

![Run one step](imgs/run_one_step.png)

Index Page
----------

From [index page](http://www.imdb.com/search/title?count=100&title_type=feature,tv_series,tv_movie&ref_=nv_ch_mm_1), we need extract two things:

* links to detail pages like `http://www.imdb.com/title/tt0167260/`
* link to [Next »](http://www.imdb.com/search/title?count=100&ref_=nv_ch_mm_1&start=101&title_type=feature,tv_series,tv_movie)

### Find Movies

As you can see, the sample handler has already extracted 1900+ links from this page. A idea of extracting detail pages is filtering links with regular expression:

```
import re
...

    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            if re.match("http://www.imdb.com/title/tt\d+/$", each.attr.href):
                self.crawl(each.attr.href, callback=self.detail_page)
```

> *`callback` is `self.detail_page` here for they have different template, we use another callback method to parse.*

Remember you can always use the power of python or anything you are familiar with to extract information. But using tools like CSS selector is recommended.

### Next page

#### CSS Selectors

CSS selectors are patterns used by [CSS] to select HTML elements which a wanted to style. As elements containing information may has different style in document, it's appropriate to use CSS Selector to select elements we wants to extract. More information about CSS selectors could be found with above links:

* [CSS Selectors](http://www.w3schools.com/css/css_selectors.asp)
* [CSS Selector Reference](http://www.w3schools.com/cssref/css_selectors.asp)

You can use CSS Selector to select elements with built-in `response.doc` object, which is provided by [PyQuery], you may get full reference there.

#### CSS Selector Helper

pyspider provide a tool called `CSS selector helper` to make it easier to generate a selector pattern to element you clicked. Enable CSS selector helper by click the button and switch to `web` panel.

![CSS Selector helper](imgs/css_selector_helper.png)

The element will highlighted in yellow when mouse over. When you click it, all elements with same CSS Selector will frame in red and add the pattern to cursor position of your code. Add following code and put cursor between the two quotation marks:

```
        self.crawl(response.doc('').attr.href, callback=self.index_page)
```

click "Next »", selector pattern should have been added to your code:

```
    def index_page(self, response):
        for each in response.doc('a[href^="http"]').items():
            if re.match("http://www.imdb.com/title/tt\d+/$", each.attr.href):
                self.crawl(each.attr.href, callback=self.detail_page)
        self.crawl(response.doc('HTML>BODY#styleguide-v2>DIV#wrapper>DIV#root>DIV#pagecontent>DIV#content-2-wide>DIV#main>DIV.leftright>DIV#right>SPAN.pagination>A').attr.href, callback=self.index_page)
```

Extracting Information
----------------------

Click `run` again and follow to detail page.

Add keys you need to result dict and collect content with the help of `CSS selector helper` repeatedly:

```
    def detail_page(self, response):
        return {
            "url": response.url,
            "title": response.doc('HTML>BODY#styleguide-v2>DIV#wrapper>DIV#root>DIV#pagecontent>DIV#content-2-wide>DIV#maindetails_center_top>DIV.article.title-overview>DIV#title-overview-widget>TABLE#title-overview-widget-layout>TBODY>TR>TD#overview-top>H1.header>SPAN.itemprop').text(),
            "rating": response.doc('HTML>BODY#styleguide-v2>DIV#wrapper>DIV#root>DIV#pagecontent>DIV#content-2-wide>DIV#maindetails_center_top>DIV.article.title-overview>DIV#title-overview-widget>TABLE#title-overview-widget-layout>TBODY>TR>TD#overview-top>DIV.star-box.giga-star>DIV.star-box-details>STRONG>SPAN').text(),
            "director": [x.text() for x in response.doc('div[itemprop="director"] span[itemprop="name"]').items()],
        }
```

Note that, `CSS Selector helper` may not always work (directors and starts have same pattern). You may need write selector pattern manually with tools like Chrome Dev Tools:

![inspect element](imgs/inspect_element.png)

You doesn't need to collect every ancestral elements, only the key elements which can differentiate with the elements you doesn't need is enough. However, it needs experience on scraping or Web developing to know which attribute is unique in the document, can be used as locator.

Running
-------

1. After tested you code, don't forget to save it.
2. Back to dashboard find your project.
3. Changing the `status` to `DEBUG` or `RUNNING`.
4. Press the `run` button. 

![index demo](imgs/index_page.png)

Notes
-----

The script is just a simple guide, you may found more issues when scraping IMDb:

* ref in listing page url is for tracing user, it's better remove it from url.
* IMDb does not serve more than 100000 results for any query, you need find more lists with lesser then 100000 results, like [this](http://www.imdb.com/search/title?genres=action&title_type=feature&sort=moviemeter,asc)
* You may need a list sorted by update time and update it with a shorter interval.
* Some attribute is hard to extract, you may need write pattern on hand or using [XPATH](http://www.w3schools.com/xpath/xpath_syntax.asp) and/or some python code to extract informations.

[IMDb]:          http://www.imdb.com/
[WWW]:           http://en.wikipedia.org/wiki/World_Wide_Web
[HTTP]:          http://en.wikipedia.org/wiki/Hypertext_Transfer_Protocol
[HTML]:          http://en.wikipedia.org/wiki/HTML
[URL]:           http://en.wikipedia.org/wiki/Uniform_resource_locator
[CSS]:           https://developer.mozilla.org/en-US/docs/Web/Guide/CSS/Getting_Started/What_is_CSS
[PyQuery]:       https://pythonhosted.org/pyquery/
