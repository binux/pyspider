Response
========

The attributes of Response object.

### Response.url

final URL.

### Response.text

Content of response, in unicode.

if `Response.encoding` is None and `chardet` module is available, encoding of content will be guessed.

### Response.content

Content of response, in bytes.

### Response.doc

A [PyQuery](https://pythonhosted.org/pyquery/) object of the response's content. Links have made as absolute by default.

Refer to the documentation of PyQuery: [https://pythonhosted.org/pyquery/](https://pythonhosted.org/pyquery/)

It's important that I will repeat, refer to the documentation of PyQuery: [https://pythonhosted.org/pyquery/](https://pythonhosted.org/pyquery/)

### Response.etree

A [lxml](http://lxml.de/) object of the response's content.

### Response.json

The JSON-encoded content of the response, if any.

### Response.status_code

### Response.orig_url

If there is any redirection during the request, here is the url you just submit via `self.crawl`.

### Response.headers

A case insensitive dict holds the headers of response.

### Response.cookies

### Response.error

Messages when fetch error

### Response.time

Time used during fetching.

### Response.ok

True if `status_code` is 200 and no error.

### Response.encoding

Encoding of Response.content.

If Response.encoding is None, encoding will be guessed by header or content or `chardet`(if available).

Set encoding of content manually will overwrite the guessed encoding.

### Response.save

The object saved by [`self.crawl`](/apis/self.crawl/#save) API

### Response.js_script_result

content returned by JS script

### Response.raise_for_status()

Raise HTTPError if status code is not 200 or `Response.error` exists.

