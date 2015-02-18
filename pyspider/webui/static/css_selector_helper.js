// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2013-11-11 18:50:58
 
(function(){
  function getElementByXpath(path) {
    return document.evaluate(path, document, null,
                             XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue;
  }

  function getOffset(elem) {
    var top = 0;
    var left = 0;
    do {
      if ( !isNaN( elem.offsetLeft) ) left += elem.offsetLeft;
      if ( !isNaN( elem.offsetTop) ) top += elem.offsetTop;
    } while( elem = elem.offsetParent )
      return {top: top, left: left};
  }
 
  function path_info(element) {
    var path = [];
    do {
      var features = [];
      // tagName
      features.push({
        name: element.tagName.toLowerCase(),
        pattern: element.tagName.toLowerCase(),
        selected: true,
      });
      // id
      if (element.getAttribute('id')) {
        features.push({
          name: '#'+element.getAttribute('id'),
          pattern: '#'+element.getAttribute('id'),
          selected: true,
        });
      }
      // class
      if (element.classList.length > 0) {
        for (var i=0; i<element.classList.length; i++) {
          features.push({
            name: '.'+element.classList[i],
            pattern: '.'+element.classList[i],
            selected: true,
          });
        }
      }
      // rel, property
      var allowed_attr_names = ('rel', 'property');
      for (var i=0, attrs = element.attributes; i < attrs.length; i++) {
        if (allowed_attr_names.indexOf(attrs[i].nodeName) == -1) {
          continue
        }
        features.push({
          name: '['+attrs[i].nodeName+'='+JSON.stringify(attrs[i].nodeValue)+']',
          pattern: '['+attrs[i].nodeName+'='+JSON.stringify(attrs[i].nodeValue)+']',
          selected: true,
        });
      }

      // get xpath
      var siblings = element.parentNode.childNodes;
      var xpath = element.tagName.toLowerCase();
      for (var i=0, ix=0; siblings.length > 1 && i < siblings.length; i++) {
        var sibling = siblings[i];
        if (sibling === element) {
          xpath += '['+(ix+1)+']';
          break;
        } else if (sibling.tagName == element.tagName) {
          ix++;
        }
      }

      // pack it up
      path.push({
        tag: element.tagName.toLowerCase(),
        name: element.tagName.toLowerCase(),
        xpath: xpath,
        selected: true,
        invalid: element.tagName.toLowerCase() === 'tbody',
        features: features,
      });
    } while (element = element.parentElement);

    path.reverse();
    return path;
  }

  function overlay(elements) {
    if (elements instanceof Element) {
      elements = [elements];
    }
    Array.prototype.forEach.call(
      document.querySelectorAll('.pyspider_overlay'),
      function(elem) {
        elem.remove();
      });
    Array.prototype.forEach.call(elements, function(elem) {
      var div = document.createElement("div");
      div.className = "pyspider_overlay";
      var offset = getOffset(elem);
      div.setAttribute('style', 'z-index: 999999;background-color: rgba(255, 165, 0, 0.3);position: absolute;pointer-events: none;'
                     +'top: '+offset.top+'px;'
                     +'left:'+offset.left+'px;'
                     +'width: '+elem.offsetWidth+'px;'
                     +'height: '+elem.offsetHeight+'px;');
      document.body.appendChild(div);
    });
  }

  function heightlight(elements) {
    if (elements instanceof Element) {
      elements = [elements];
    }
    Array.prototype.forEach.call(
      document.querySelectorAll('.pyspider_highlight'),
      function(elem) {
        elem.remove();
      });
    Array.prototype.forEach.call(elements, function(elem) {
      var div = document.createElement("div");
      div.className = "pyspider_highlight";
      var offset = getOffset(elem);
      div.setAttribute('style', 'z-index: 888888;border: 2px solid #c00;position: absolute;pointer-events: none;'
                     +'top: '+offset.top+'px;'
                     +'left:'+offset.left+'px;'
                     +'width: '+elem.offsetWidth+'px;'
                     +'height: '+elem.offsetHeight+'px;');
      document.body.appendChild(div);
    });
  }

  window.addEventListener("message", function(ev) {
    if (ev.data.type == "overlay") {
      console.log(ev.data.xpath, getElementByXpath(ev.data.xpath));
      overlay(getElementByXpath(ev.data.xpath));
    }
  });

  document.addEventListener("mouseover", function(ev) {
    overlay(event.target);
  });
 
  document.addEventListener("click", function(ev) {
    ev.preventDefault();
    ev.stopPropagation();

    parent.postMessage({type: 'selector_helper_click', path: path_info(ev.target)}, '*');
  });
})();
