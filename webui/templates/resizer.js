// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-03-16 11:05:05

window.addEventListener('load', function() {
  var height = document.body.scrollHeight;
  var iframe = document.createElement('iframe');
  iframe.height = 0;
  iframe.width = 0;
  iframe.frameborder = 0;
  iframe.src = "http://{{ host }}/helper/resizer.html?height="+height+"&nocache="+(new Date()).getTime();
  document.body.appendChild(iframe);
});
