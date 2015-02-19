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

  function merge_name(features) {
    var element_name = '';
    features.forEach(function(f) {
      if (f.selected)
        element_name += f.name;
    })
    return element_name;
  }

  function merge_pattern(path) {
    var pattern = '';
    var prev = null;
    path.forEach(function(p) {
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
        pattern += ' '+element_pattern;
        prev = p;
      } else {
        prev = null;
      }
    })
    return pattern;
  }
 
  function path_info(element) {
    var path = [];
    do {
      var features = [];
      var has_id_feature = false;
      var has_class_feature = false;
      // tagName
      features.push({
        name: element.tagName.toLowerCase(),
        pattern: element.tagName.toLowerCase(),
        selected: false,
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
        var min_class_name = null, min_class_cnt = 9999;
        for (var i=0; i<element.classList.length; i++) {
          var class_name = element.classList[i];
          var class_cnt = document.getElementsByClassName(class_name).length;
          if (!min_class_name || min_class_cnt > class_cnt) {
            min_class_name = class_name;
            min_class_cnt = class_cnt;
          }

          features.push({
            name: '.'+class_name,
            pattern: '.'+class_name,
            selected: false,
          });
        }
        if (!has_id_feature && min_class_name) {
          for (var i=0; i<features.length; i++) {
            if (features[i].pattern == '.'+min_class_name) {
              features[i].selected = true;
              has_class_feature = true;
              break;
            }
          }
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
          selected: !has_id_feature && !has_class_feature,
        });
      }
      if (!has_id_feature && !has_class_feature) {
        features[0].selected = true;
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

    // select features
    var pattern = merge_pattern(path);
    var selected_elements = document.querySelectorAll(pattern);
    path.forEach(function(p) {
      if (p.invalid)
        return;
      p.selected = false;
      if (selected_elements.length == document.querySelectorAll(
        merge_pattern(path)).length) {
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
                     +'top: '+offset.top+'px;'
                     +'left:'+offset.left+'px;'
                     +'width: '+elem.offsetWidth+'px;'
                     +'height: '+elem.offsetHeight+'px;');
      document.body.appendChild(div);
    });
  }

  window.addEventListener("message", function(ev) {
    if (ev.data.type == "overlay") {
      //console.log(ev.data.xpath, getElementByXpath(ev.data.xpath));
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
