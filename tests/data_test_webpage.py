#!/usr/bin/env python
# -*- encoding: utf-8 -*-
# vim: set et sw=4 ts=4 sts=4 ff=unix fenc=utf8:
# Author: Binux<roy@binux.me>
#         http://binux.me
# Created on 2015-01-24 13:44:10

from httpbin import app

@app.route('/pyspider/test.html')
def test_page():
    return '''
<a href="/404">404
<a href="/links/10/0">0
<a href="/links/10/1">1
<a href="/links/10/2">2
<a href="/links/10/3">3
<a href="/links/10/4">4
<a href="/gzip">gzip
<a href="/get">get
<a href="/deflate">deflate
<a href="/html">html
<a href="/xml">xml
<a href="/robots.txt">robots
<a href="/cache">cache
<a href="/stream/20">stream
'''

@app.route('/pyspider/ajax.html')
def test_ajax():
    return '''
<div class=status>loading...</div>
<div class=ua></div>
<div class=ip></div>
<script>
var xhr = new XMLHttpRequest();
xhr.onload = function() {
  var data = JSON.parse(xhr.responseText);
  document.querySelector('.status').innerHTML = 'done';
  document.querySelector('.ua').innerHTML = data.headers['User-Agent'];
  document.querySelector('.ip').innerHTML = data.origin;
}
xhr.open("get", "/get", true);
xhr.send();
</script>
'''

@app.route('/pyspider/ajax_click.html')
def test_ajax_click():
    return '''
<div class=status>loading...</div>
<div class=ua></div>
<div class=ip></div>
<a href="javascript:void(0)" onclick="load()">load</a>
<script>
function load() {
    var xhr = new XMLHttpRequest();
    xhr.onload = function() {
      var data = JSON.parse(xhr.responseText);
      document.querySelector('.status').innerHTML = 'done';
      document.querySelector('.ua').innerHTML = data.headers['User-Agent'];
      document.querySelector('.ip').innerHTML = data.origin;
    }
    xhr.open("get", "/get", true);
    xhr.send();
}
</script>
'''
