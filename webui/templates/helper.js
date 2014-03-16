// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-03-16 11:05:05

(function() {
  window.addEventListener('load', function() {
    var height = document.body.scrollHeight;
    parent.postMessage({type: 'resize', height: height}, '*');
  });

  var css_helper_enabled = false;
  window.addEventListener("message", function(ev) {
    if (!css_helper_enabled && ev.data.type == "enable_css_selector_helper") {
      var script = document.createElement("script");
      script.src = "http://{{ host }}/static/css_selector_helper.js";
      document.body.appendChild(script);
      css_helper_enabled = true;
    }
  }, false);
})();
