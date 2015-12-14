// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-10-29 22:12:14

var port, server, service,
  wait_before_end = 1000,
  system = require('system'),
  webpage = require('webpage');

if (system.args.length !== 2) {
  console.log('Usage: simpleserver.js <portnumber>');
  phantom.exit(1);
} else {
  port = system.args[1];
  server = require('webserver').create();
  console.debug = function(){};

  service = server.listen(port, {
    'keepAlive': false
  }, function (request, response) {
    phantom.clearCookies();

    //console.debug(JSON.stringify(request, null, 4));
    // check method
    if (request.method == 'GET') {
      body = "method not allowed!";
      response.statusCode = 403;
      response.headers = {
        'Cache': 'no-cache',
        'Content-Length': body.length
      };
      response.write(body);
      response.closeGracefully();
      return;
    }
    
    var first_response = null,
        finished = false,
        page_loaded = false,
        start_time = Date.now(),
        end_time = null,
        script_executed = false,
        script_result = null;

    var fetch = JSON.parse(request.postRaw);
    console.debug(JSON.stringify(fetch, null, 2));

    // create and set page
    var page = webpage.create();
    page.onConsoleMessage = function(msg) {
        console.log('console: ' + msg);
    };
    page.viewportSize = {
      width: fetch.js_viewport_width || 1024,
      height: fetch.js_viewport_height || 768*3
    }
    if (fetch.headers) {
      fetch.headers['Accept-Encoding'] = undefined;
      fetch.headers['Connection'] = undefined;
      fetch.headers['Content-Length'] = undefined;
    }
    if (fetch.headers && fetch.headers['User-Agent']) {
      page.settings.userAgent = fetch.headers['User-Agent'];
    }
    // this may cause memory leak: https://github.com/ariya/phantomjs/issues/12903
    page.settings.loadImages = fetch.load_images === undefined ? true : fetch.load_images;
    page.settings.resourceTimeout = fetch.timeout ? fetch.timeout * 1000 : 120*1000;
    if (fetch.headers) {
      page.customHeaders = fetch.headers;
    }

    // add callbacks
    page.onInitialized = function() {
      if (!script_executed && fetch.js_script && fetch.js_run_at === "document-start") {
        script_executed = true;
        console.log('running document-start script.');
        script_result = page.evaluateJavaScript(fetch.js_script);
      }
    };
    page.onLoadFinished = function(status) {
      page_loaded = true;
      if (!script_executed && fetch.js_script && fetch.js_run_at !== "document-start") {
        script_executed = true;
        console.log('running document-end script.');
        script_result = page.evaluateJavaScript(fetch.js_script);
      }
      console.debug("waiting "+wait_before_end+"ms before finished.");
      end_time = Date.now() + wait_before_end;
      setTimeout(make_result, wait_before_end+10, page);
    };
    page.onResourceRequested = function(request) {
      console.debug("Starting request: #"+request.id+" ["+request.method+"]"+request.url);
      end_time = null;
    };
    page.onResourceReceived = function(response) {
      console.debug("Request finished: #"+response.id+" ["+response.status+"]"+response.url);
      if (first_response === null && response.status != 301 && response.status != 302) {
        first_response = response;
      }
      if (page_loaded) {
        console.debug("waiting "+wait_before_end+"ms before finished.");
        end_time = Date.now() + wait_before_end;
        setTimeout(make_result, wait_before_end+10, page);
      }
    }
    page.onResourceError = page.onResourceTimeout=function(response) {
      console.info("Request error: #"+response.id+" ["+response.errorCode+"="+response.errorString+"]"+response.url);
      if (first_response === null) {
        first_response = response;
      }
      if (page_loaded) {
        console.debug("waiting "+wait_before_end+"ms before finished.");
        end_time = Date.now() + wait_before_end;
        setTimeout(make_result, wait_before_end+10, page);
      }
    }

    // make sure request will finished
    setTimeout(function(page) {
      make_result(page);
    }, page.settings.resourceTimeout + 100, page);

    // send request
    page.open(fetch.url, {
      operation: fetch.method,
      data: fetch.data,
    });

    // make response
    function make_result(page) {
      if (finished) {
        return;
      }
      if (Date.now() - start_time < page.settings.resourceTimeout) {
        if (!!!end_time) {
          return;
        }
        if (end_time > Date.now()) {
          setTimeout(make_result, Date.now() - end_time, page);
          return;
        }
      }

      var result = {};
      try {
        result = _make_result(page);
      } catch (e) {
        result = {
          orig_url: fetch.url,
          status_code: 599,
          error: e.toString(),
          content:  '',
          headers: {},
          url: page.url,
          cookies: {},
          time: (Date.now() - start_time) / 1000,
          save: fetch.save
        }
      }

      page.close();
      finished = true;
      console.log("["+result.status_code+"] "+result.orig_url+" "+result.time)

      var body = JSON.stringify(result, null, 2);
      response.writeHead(200, {
        'Cache': 'no-cache',
        'Content-Type': 'application/json',
      });
      response.write(body);
      response.closeGracefully();
    }

    function _make_result(page) {
      if (first_response === null) {
        throw "No response received!";
      }

      var cookies = {};
      page.cookies.forEach(function(e) {
        cookies[e.name] = e.value;
      });

      var headers = {};
      if (first_response.headers) {
        first_response.headers.forEach(function(e) {
          headers[e.name] = e.value;
        });
      }

      return {
        orig_url: fetch.url,
        status_code: first_response.status || 599,
        error: first_response.errorString,
        content:  page.content,
        headers: headers,
        url: page.url,
        cookies: cookies,
        time: (Date.now() - start_time) / 1000,
        js_script_result: script_result,
        save: fetch.save
      }
    }
  });

  if (service) {
    console.log('Web server running on port ' + port);
  } else {
    console.log('Error: Could not create web server listening on port ' + port);
    phantom.exit();
  }
}
