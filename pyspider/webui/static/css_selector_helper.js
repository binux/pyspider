// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2013-11-11 18:50:58
 
(function(){
  function getOffset(elem) {
    var top = 0;
    var left = 0;
    do {
      if ( !isNaN( elem.offsetLeft) ) left += elem.offsetLeft;
      if ( !isNaN( elem.offsetTop) ) top += elem.offsetTop;
    } while( elem = elem.offsetParent )
      return {top: top, left: left};
  }
 
  var ballowed_tag = ['ul', 'li', 'a', 'ol', 'table', 'tr', 'dd', 'dt', 'dl', 'h1', 'h2', 'h3', 'h4', 'b', 'i', 'strong', 'em', 'img', 'code', 'small'];
  function get_selector(element, need_tagName) {
    need_tagName = need_tagName === undefined ? true : false;
    var _getSelector = function(element, need_tagName) {
      var result = '';
      // fix tbody
      if (element.tagName == 'TBODY') {
        return 'TBODY';
      }
      if (need_tagName) {
        result += element.tagName;
      } else if (ballowed_tag.indexOf(element.tagName.toLowerCase()) != -1) {
        result += element.tagName;
      }
 
      if (element.getAttribute('id') && element.getAttribute('id').match(/^[a-zA-Z]+/)) {
        return result+'#'+element.getAttribute('id');
      } else if (element.classList.length > 0) {
        for(var i=0; i<element.classList.length; i++) {
          if (element.classList[i] == 'current') continue;
          if (element.classList[i] == 'active') continue;
          result += '.'+element.classList[i];
        }
      }
      return result;
    };
 
    var result = [];
    result.push(_getSelector(element, need_tagName));
    while( element = element.parentElement ) {
      var selector = _getSelector(element, need_tagName);
      if (selector !== '')
        result.push(selector);
      else
        result.push('*');
    }
    result.reverse();
    return result.join('>').replace(/>TBODY>/g, " ");
  };
 
  var overlay = document.createElement("div");
  overlay.style.display = "none";
  document.body.appendChild(overlay);
 
  document.addEventListener("mouseover", function(ev) {
    var offset = getOffset(event.target);
    overlay.setAttribute('style', 'z-index: 999999;background-color: rgba(255, 165, 0, 0.3);position: absolute;pointer-events: none;'
                     +'top: '+offset.top+'px;'
                     +'left:'+offset.left+'px;'
                     +'width: '+event.target.offsetWidth+'px;'
                     +'height: '+event.target.offsetHeight+'px;');
  });
 
  document.addEventListener("click", function(ev) {
    ev.preventDefault();
    ev.stopPropagation();
    var selector = get_selector(ev.target);
    Array.prototype.forEach.call(document.querySelectorAll('.binux_click_highlight'), function(elem) {
      elem.remove();
    });
    Array.prototype.forEach.call(document.querySelectorAll(selector), function(elem) {
      var div = document.createElement("div");
      div.className = "binux_click_highlight";
      var offset = getOffset(elem);
      div.setAttribute('style', 'z-index: 88888;border: 2px solid #c00;position: absolute;pointer-events: none;'
                     +'top: '+(offset.top-2)+'px;'
                     +'left:'+(offset.left-2)+'px;'
                     +'width: '+elem.offsetWidth+'px;'
                     +'height: '+elem.offsetHeight+'px;');
      document.body.appendChild(div);
    });
    parent.postMessage({type: 'selector', selector: selector}, '*');
  });
})();
