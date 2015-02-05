Response
========

The attributes of Response object.

### Response.url

final URL

### Response.text

Content of the response, in unicode.

if `Response.encoding` is None and `chardet` module is available, encoding will be guessed.

### Response.doc

A [PyQuery](https://pythonhosted.org/pyquery/) object of the request's content. `make_links_absolute` is called by default.

### Response.json

The json-encoded content of the response, if any.

### Response.status_code

### Response.orig_url

### Response.headers

### Response.cookies

### Response.error

Fetch error

### Response.time

Fetch time

### Response.ok

True if `status_code` is 200 and no error.

### Response.encoding

Encoding of Response.content.

If Response.encoding is None, encoding will be guessed by header or content or chardet if available.

Set encoding of content manually will overwrite the guessed encoding.

### Response.content

### Response.save

The object saved by [`self.crawl`](/apis/self.crawl/#process) API

### Response.js_script_result

content returned by JS script

### Response.raise_for_status()
