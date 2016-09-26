// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2013-11-11 18:50:58
 
(function(){
  function arrayEquals(a, b) {
    if (!a || !b)
      return false;
    if (a.length != b.length)
      return false;

    for (var i = 0, l = a.length; i < l; i++) {
      if (a[i] !== b[i])
        return false;
    }
    return true;
  }
  
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

  function merge_name(features) {
    var element_name = '';
    features.forEach(function(f) {
      if (f.selected)
        element_name += f.name;
    })
    return element_name;
  }

  function merge_pattern(path, end) {
    var pattern = '';
    var prev = null;
    path.forEach(function(p, i) {
      if (end >= 0 && i > end) {
        return;
      }
      if (p.invalid) {
        prev = null;
      } else if (p.selected) {
        if (prev) {
          pattern += ' >';
        }
        var element_pattern = '';
        p.features.forEach(function(f) {
          if (f.selected) {
            element_pattern += f.pattern;
          }
        });
        if (element_pattern === '') {
          element_pattern = '*';
        }
        pattern += ' '+element_pattern;
        prev = p;
      } else {
        prev = null;
      }
    })
    if (pattern === '') {
      pattern = '*';
    }
    return pattern;
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
        has_id_feature = true;
        features.push({
          name: '#'+element.getAttribute('id'),
          pattern: '#'+element.getAttribute('id'),
          selected: true,
        });
      }
      // class
      if (element.classList.length > 0) {
        for (var i=0; i<element.classList.length; i++) {
          var class_name = element.classList[i];
          features.push({
            name: '.'+class_name,
            pattern: '.'+class_name,
            selected: true,
          });
        }
      }
      // rel, property
      var allowed_attr_names = ('rel', 'property', 'itemprop');
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
        name: merge_name(features),
        xpath: xpath,
        selected: true,
        invalid: element.tagName.toLowerCase() === 'tbody',
        features: features,
      });
    } while (element = element.parentElement);

    path.reverse();

    // select elements
    var selected_elements = document.querySelectorAll(merge_pattern(path));
    path.forEach(function(p, i) {
      if (p.invalid)
        return;
      // select features
      var feature_selected_elements = document.querySelectorAll(merge_pattern(path, i));
      p.features.forEach(function(f, fi) {
        f.selected = false;
        if (arrayEquals(feature_selected_elements,
                        document.querySelectorAll(merge_pattern(path, i)))) {
          return;
        }
        f.selected = true;
      });
      if (p.features.every(function(f) {
        return !f.selected;
      })) {
        p.features[0].selected = true;
      }
      p.name = merge_name(p.features);
    });

    path.forEach(function(p, i) {
      p.selected = false;
      if (arrayEquals(selected_elements,
                      document.querySelectorAll(merge_pattern(path)))) {
        p.name = p.tag;
        return;
      }
      p.selected = true;
    });

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
                     +'top: '+(offset.top-2)+'px;'
                     +'left:'+(offset.left-2)+'px;'
                     +'width: '+elem.offsetWidth+'px;'
                     +'height: '+elem.offsetHeight+'px;');
      document.body.appendChild(div);
    });
  }

  window.addEventListener("message", function(ev) {
    if (ev.data.type == "overlay") {
      //console.log(ev.data.xpath, getElementByXpath(ev.data.xpath));
      overlay(getElementByXpath(ev.data.xpath));
    } else if (ev.data.type == "heightlight") {
      heightlight(document.querySelectorAll(ev.data.css_selector));
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
