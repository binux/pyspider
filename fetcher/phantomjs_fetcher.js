// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-10-29 22:12:14

var port, server, service,
  system = require('system'),
  webpage = require('webpage');


if (system.args.length !== 2) {
  console.log('Usage: simpleserver.js <portnumber>');
  phantom.exit(1);
} else {
  port = system.args[1];
  server = require('webserver').create();

  service = server.listen(port, function (request, response) {
    //console.log(JSON.stringify(request, null, 4));
    // check method
    if (request.method == 'GET') {
      response.statusCode = 403;
      response.write("method not allowed!");
      response.close();
      return;
    }

    var fetch = JSON.parse(request.postRaw);
    console.log(JSON.stringify(fetch, null, 2));

    // create and set page
    var page = webpage.create();
    page.viewportSize = {
      width: 1024,
      height: 768
    }
    if (fetch.headers && fetch.headers['User-Agent']) {
      page.settings.userAgent = fetch.headers['User-Agent'];
    }
    page.settings.loadImages = fetch.load_images ? true : false;
    page.settings.resourceTimeout = fetch.timeout ? fetch.timeout * 1000 : 120*1000;
    if (fetch.headers) {
      page.customHeaders = fetch.headers;
    }
    
    // add callbacks
    var first_response = null,
        page_loaded = false,
        start_time = Date.now(),
        end_time = null;
    page.onInitialized = function() {
      if (fetch.js_script && fetch.js_run_at === "document-start") {
        page.evaluateJavaScript(fetch.js_script);
      }
    };
    page.onLoadFinished = function(status) {
      page_loaded = true;
      if (status !== "success") {
        return;
      }
      if (fetch.js_script && fetch.js_run_at !== "document-start") {
        page.evaluateJavaScript(fetch.js_script);
      }
      end_time = Date.now() + 300;
      setTimeout(make_result, 310, page);
    };
    page.onResourceRequested = function() {
      end_time = null;
    };
    page.onResourceReceived = function(response) {
      if (first_response === null) {
        first_response = response;
      }
      if (page_loaded) {
        end_time = Date.now() + 300;
        setTimeout(make_result, 310, page);
      }
    }
    page.onResourceError=page.onResourceTimeout=function() {
      if (page_loaded) {
        end_time = Date.now() + 300;
        setTimeout(make_result, 310, page);
      }
    }

    // send request
    page.open(fetch.url, {
      operation: fetch.method,
      data: fetch.data,
    });

    // make response
    function make_result(page) {
      if (!!!end_time) {
        return;
      }
      if (end_time > Date.now()) {
        setTimeout(make_result, Date.now() - end_time, page);
        return;
      }

      var cookies = {};
      page.cookies.forEach(function(e) {
        cookies[e.name] = e.value;
      });

      var result = {
        orig_url: fetch.url,
        content: page.content,
        headers: first_response.headers,
        status_code: first_response.status,
        url: page.url,
        cookies: cookies,
        time: (end_time - start_time) / 1000,
        save: fetch.save
      }

      var body = JSON.stringify(result, null, 2);
      response.statusCode = 200;
      response.headers = {
        'Cache': 'no-cache',
        'Content-Type': 'application/json',
      };
      response.write(body);
      response.closeGracefully();
    }
  });

  if (service) {
    console.log('Web server running on port ' + port);
  } else {
    console.log('Error: Could not create web server listening on port ' + port);
    phantom.exit();
  }
}
