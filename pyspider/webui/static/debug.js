/******/ (function(modules) { // webpackBootstrap
/******/ 	// The module cache
/******/ 	var installedModules = {};
/******/
/******/ 	// The require function
/******/ 	function __webpack_require__(moduleId) {
/******/
/******/ 		// Check if module is in cache
/******/ 		if(installedModules[moduleId])
/******/ 			return installedModules[moduleId].exports;
/******/
/******/ 		// Create a new module (and put it into the cache)
/******/ 		var module = installedModules[moduleId] = {
/******/ 			exports: {},
/******/ 			id: moduleId,
/******/ 			loaded: false
/******/ 		};
/******/
/******/ 		// Execute the module function
/******/ 		modules[moduleId].call(module.exports, module, module.exports, __webpack_require__);
/******/
/******/ 		// Flag the module as loaded
/******/ 		module.loaded = true;
/******/
/******/ 		// Return the exports of the module
/******/ 		return module.exports;
/******/ 	}
/******/
/******/
/******/ 	// expose the modules object (__webpack_modules__)
/******/ 	__webpack_require__.m = modules;
/******/
/******/ 	// expose the module cache
/******/ 	__webpack_require__.c = installedModules;
/******/
/******/ 	// __webpack_public_path__
/******/ 	__webpack_require__.p = "";
/******/
/******/ 	// Load entry module and return exports
/******/ 	return __webpack_require__(0);
/******/ })
/************************************************************************/
/******/ ([
/* 0 */
/***/ function(module, exports, __webpack_require__) {

	"use strict";
	
	__webpack_require__(3);
	
	__webpack_require__(7);
	
	// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
	// Author: Binux<i@binux.me>
	//         http://binux.me
	// Created on 2014-02-23 15:19:19
	
	window.SelectorHelper = function () {
	  var helper = $('#css-selector-helper');
	
	  function merge_name(p) {
	    var features = p.features;
	    var element_name = '';
	    features.forEach(function (f) {
	      if (f.selected) element_name += f.name;
	    });
	    if (element_name === '') {
	      return p.tag;
	    }
	    return element_name;
	  }
	
	  function merge_pattern(path, end) {
	    var pattern = '';
	    var prev = null;
	    path.forEach(function (p, i) {
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
	        p.features.forEach(function (f) {
	          if (f.selected) {
	            element_pattern += f.pattern;
	          }
	        });
	        if (element_pattern === '') {
	          element_pattern = '*';
	        }
	        pattern += ' ' + element_pattern;
	        prev = p;
	      } else {
	        prev = null;
	      }
	    });
	    if (pattern === '') {
	      pattern = '*';
	    }
	    return pattern.trim();
	  }
	
	  function selector_changed(path) {
	    $("#tab-web iframe").get(0).contentWindow.postMessage({
	      type: "heightlight",
	      css_selector: merge_pattern(path)
	    }, '*');
	  }
	
	  var current_path = null;
	  function render_selector_helper(path) {
	    helper.find('.element').remove();
	    var elements = [];
	    $.each(path, function (i, p) {
	      var span = $('<span>').addClass('element').data('info', p);
	      $('<span class="element-name">').text(p.name).appendTo(span);
	      if (p.selected) span.addClass('selected');
	      if (p.invalid) span.addClass('invalid');
	
	      var ul = $('<ul>');
	      $.each(p.features, function (i, f) {
	        var li = $('<li>').text(f.name).data('feature', f);
	        if (f.selected) li.addClass('selected');
	        li.appendTo(ul);
	        // feature on click
	        li.on('click', function (ev) {
	          ev.stopPropagation();
	          var $this = $(this);
	          var f = $this.data('feature');
	          if (f.selected) {
	            f.selected = false;
	            $this.removeClass('selected');
	          } else {
	            f.selected = true;
	            $this.addClass('selected');
	          }
	          var element = $this.parents('.element');
	          if (!p.selected) {
	            p.selected = true;
	            element.addClass('selected');
	          }
	          element.find('.element-name').text(merge_name(p));
	          selector_changed(path);
	        });
	      });
	      ul.appendTo(span);
	
	      span.on('mouseover', function (ev) {
	        var xpath = [];
	        $.each(path, function (i, _p) {
	          xpath.push(_p.xpath);
	          if (_p === p) {
	            return false;
	          }
	        });
	        $("#tab-web iframe")[0].contentWindow.postMessage({
	          type: 'overlay',
	          xpath: '/' + xpath.join('/')
	        }, '*');
	      });
	      // path on click
	      span.on('click', function (ev) {
	        ev.stopPropagation();
	        var $this = $(this);
	        var p = $this.data('info');
	        if (p.selected) {
	          p.selected = false;
	          $this.removeClass('selected');
	        } else {
	          p.selected = true;
	          $this.addClass('selected');
	        }
	        $this.find('.element-name').text(merge_name($this.data('info')));
	        selector_changed(path);
	      });
	      elements.push(span);
	    });
	    helper.prepend(elements);
	
	    adjustHelper();
	    selector_changed(path);
	  }
	
	  function adjustHelper() {
	    while (helper[0].scrollWidth > helper.width()) {
	      var e = helper.find('.element:visible:first');
	      if (e.length == 0) {
	        return;
	      }
	      e.addClass('invalid').data('info')['invalid'] = true;
	    }
	  }
	
	  var tab_web = $('#tab-web');
	  return {
	    init: function init() {
	      var _this = this;
	      _this.clear();
	      window.addEventListener("message", function (ev) {
	        if (ev.data.type == "selector_helper_click") {
	          console.log(ev.data.path);
	          render_selector_helper(ev.data.path);
	          current_path = ev.data.path;
	        }
	      });
	
	      $("#J-enable-css-selector-helper").on('click', function () {
	        _this.clear();
	        $("#tab-web iframe")[0].contentWindow.postMessage({
	          type: 'enable_css_selector_helper'
	        }, '*');
	        _this.enable();
	      });
	
	      $("#task-panel").on("scroll", function (ev) {
	        if (!helper.is(':visible')) {
	          return;
	        }
	        if ($("#debug-tabs").position().top < 0) {
	          helper.addClass('fixed');
	          tab_web.addClass('fixed');
	        } else {
	          helper.removeClass('fixed');
	          tab_web.removeClass('fixed');
	        }
	      });
	
	      // copy button
	      var input = helper.find('.copy-selector-input');
	      input.on('focus', function (ev) {
	        $(this).select();
	      });
	      helper.find('.copy-selector').on('click', function (ev) {
	        if (!current_path) {
	          return;
	        }
	        if (input.is(':visible')) {
	          input.hide();
	          helper.find('.element').show();
	        } else {
	          helper.find('.element').hide();
	          input.val(merge_pattern(current_path)).show();
	        }
	      });
	
	      // add button
	      helper.find('.add-to-editor').on('click', function (ev) {
	        Debugger.python_editor_replace_selection(merge_pattern(current_path));
	      });
	    },
	    clear: function clear() {
	      current_path = null;
	      helper.hide();
	      helper.removeClass('fixed');
	      tab_web.removeClass('fixed');
	      helper.find('.element').remove();
	    },
	    enable: function enable() {
	      helper.show();
	      helper.find('.copy-selector-input').hide();
	      if ($("#debug-tabs").position().top < 0) {
	        helper.addClass('fixed');
	        tab_web.addClass('fixed');
	      } else {
	        helper.removeClass('fixed');
	        tab_web.removeClass('fixed');
	      }
	    }
	  };
	}();
	
	window.Debugger = function () {
	  var tmp_div = $('<div>');
	  function escape(text) {
	    return tmp_div.text(text).html();
	  }
	
	  window.addEventListener("message", function (ev) {
	    if (ev.data.type == "resize") {
	      $("#tab-web iframe").height(ev.data.height + 60);
	    }
	  });
	
	  return {
	    init: function init() {
	      //init resizer
	      this.splitter = $(".debug-panel:not(:first)").splitter().data('splitter').trigger('init').on('resize-start', function () {
	        $('#left-area .overlay').show();
	      }).on('resize-end', function () {
	        $('#left-area .overlay').hide();
	      });
	
	      //codemirror
	      CodeMirror.keyMap.basic.Tab = 'indentMore';
	      this.init_python_editor($("#python-editor"));
	      this.init_task_editor($("#task-editor"));
	      this.bind_debug_tabs();
	      this.bind_run();
	      this.bind_save();
	      this.bind_others();
	
	      // css selector helper
	      SelectorHelper.init();
	    },
	
	    not_saved: false,
	    init_python_editor: function init_python_editor($el) {
	      var _this = this;
	      this.python_editor_elem = $el;
	      var cm = this.python_editor = CodeMirror($el[0], {
	        value: script_content,
	        mode: "python",
	        indentUnit: 4,
	        lineWrapping: true,
	        styleActiveLine: true,
	        autofocus: true
	      });
	      cm.on('focus', function () {
	        $el.addClass("focus");
	      });
	      cm.on('blur', function () {
	        $el.removeClass("focus");
	      });
	      cm.on('change', function () {
	        _this.not_saved = true;
	      });
	      window.addEventListener('beforeunload', function (e) {
	        if (_this.not_saved) {
	          var returnValue = "You have not saved changes.";
	          (e || window.event).returnValue = returnValue;
	          return returnValue;
	        }
	      });
	    },
	
	    python_editor_replace_selection: function python_editor_replace_selection(content) {
	      this.python_editor.getDoc().replaceSelection(content);
	    },
	
	    auto_format: function auto_format(cm) {
	      var pos = cm.getCursor(true);
	      CodeMirror.commands.selectAll(cm);
	      cm.autoFormatRange(cm.getCursor(true), cm.getCursor(false));
	      cm.setCursor(pos);
	    },
	
	    format_string: function format_string(value, mode) {
	      var div = document.createElement('div');
	      var cm = CodeMirror(div, {
	        value: value,
	        mode: mode
	      });
	      this.auto_format(cm);
	      return cm.getDoc().getValue();
	    },
	
	    init_task_editor: function init_task_editor($el) {
	      var cm = this.task_editor = CodeMirror($el[0], {
	        value: task_content,
	        mode: "application/json",
	        indentUnit: 2,
	        lineWrapping: true,
	        styleActiveLine: true
	      });
	      this.auto_format(cm);
	      cm.getDoc().clearHistory();
	      cm.on('focus', function () {
	        $el.addClass("focus");
	      });
	      cm.on('blur', function () {
	        $el.removeClass("focus");
	      });
	    },
	
	    bind_debug_tabs: function bind_debug_tabs() {
	      var _this = this;
	      $('#tab-control > li[data-id]').on('click', function () {
	        $('#tab-control > li[data-id]').removeClass('active');
	        var name = $(this).addClass('active').data('id');
	        $('#debug-tabs .tab').hide();
	        $('#debug-tabs #' + name).show();
	      });
	      $("#tab-control li[data-id=tab-html]").on('click', function () {
	        if (!!!$("#tab-html").data("format")) {
	          var html_styled = "";
	          CodeMirror.runMode(_this.format_string($("#tab-html pre").text(), 'text/html'), 'text/html', function (text, classname) {
	            if (classname) html_styled += '<span class="cm-' + classname + '">' + escape(text) + '</span>';else html_styled += escape(text);
	          });
	          $("#tab-html pre").html(html_styled);
	          $("#tab-html").data("format", true);
	        }
	      });
	    },
	
	    bind_run: function bind_run() {
	      var _this = this;
	      $('#run-task-btn').on('click', function () {
	        _this.run();
	      });
	      $('#undo-btn').on('click', function (ev) {
	        _this.task_editor.execCommand('undo');
	      });
	      $('#redo-btn').on('click', function (ev) {
	        _this.task_editor.execCommand('redo');
	      });
	    },
	
	    bind_save: function bind_save() {
	      var _this = this;
	      $('#save-task-btn').on('click', function () {
	        var script = _this.python_editor.getDoc().getValue();
	        $('#right-area .overlay').show();
	        $.ajax({
	          type: "POST",
	          url: location.pathname + '/save',
	          data: {
	            script: script
	          },
	          success: function success(data) {
	            console.log(data);
	            _this.python_log('');
	            _this.python_log("saved!");
	            _this.not_saved = false;
	            $('#right-area .overlay').hide();
	          },
	          error: function error(xhr, textStatus, errorThrown) {
	            console.log(xhr, textStatus, errorThrown);
	            _this.python_log("save error!\n" + xhr.responseText);
	            $('#right-area .overlay').hide();
	          }
	        });
	      });
	    },
	
	    bind_follows: function bind_follows() {
	      var _this = this;
	      $('.newtask').on('click', function () {
	        if ($(this).next().hasClass("task-show")) {
	          $(this).next().remove();
	          return;
	        }
	        var task = $(this).after('<div class="task-show"><pre class="cm-s-default"></pre></div>').data("task");
	        task = JSON.stringify(window.newtasks[task], null, '  ');
	        CodeMirror.runMode(task, 'application/json', $(this).next().find('pre')[0]);
	      });
	
	      $('.newtask .task-run').on('click', function (event) {
	        event.preventDefault();
	        event.stopPropagation();
	        var task = $(this).parents('.newtask').data("task");
	        task = JSON.stringify(window.newtasks[task], null, '  ');
	        _this.task_editor.setValue(task);
	        _this.run();
	      });
	    },
	
	    bind_others: function bind_others() {
	      var _this = this;
	      $('#python-log-show').on('click', function () {
	        if ($('#python-log pre').is(":visible")) {
	          $('#python-log pre').hide();
	          $(this).height(8);
	        } else {
	          $('#python-log pre').show();
	          $(this).height(0);
	        }
	      });
	      $('.webdav-btn').on('click', function () {
	        _this.toggle_webdav_mode(this);
	      });
	    },
	
	    render_html: function render_html(html, base_url, block_script, resizer, selector_helper) {
	      if (html === undefined) {
	        html = '';
	      }
	      html = html.replace(/(\s)src=/g, "$1____src____=");
	      var dom = document.createElement('html');
	      dom.innerHTML = html;
	      if (block_script) {
	        $(dom).find('script').attr('type', 'text/plain');
	      }
	      if (resizer) {
	        $(dom).find('body').append('<script src="' + location.protocol + '//' + location.host + '/helper.js">');
	      }
	      if (selector_helper) {
	        $(dom).find('body').append('<script src="' + location.protocol + '//' + location.host + '/static/css_selector_helper.js">');
	      }
	      $(dom).find('base').remove();
	      $(dom).find('head').append('<base>');
	      $(dom).find('base').attr('href', base_url);
	      $(dom).find('link[href]').each(function (i, e) {
	        e = $(e);
	        try {
	          e.attr('href', URI(e.attr('href')).absoluteTo(base_url).toString());
	        } catch (error) {
	          console.log(error);
	        }
	      });
	      $(dom).find('img[____src____]').each(function (i, e) {
	        e = $(e);
	        try {
	          e.attr('____src____', URI(e.attr('____src____')).absoluteTo(base_url).toString());
	        } catch (error) {
	          console.log(error);
	        }
	      });
	      html = dom.innerHTML;
	      html = html.replace(/(\s)____src____=/g, "$1src=");
	      return encodeURI("data:text/html;charset=utf-8," + html);
	    },
	
	    run: function run() {
	      var script = this.python_editor.getDoc().getValue();
	      var task = this.task_editor.getDoc().getValue();
	      var _this = this;
	
	      // reset
	      SelectorHelper.clear();
	      $("#tab-web .iframe-box").html('');
	      $("#tab-html pre").html('');
	      $('#tab-follows').html('');
	      $("#tab-control li[data-id=tab-follows] .num").hide();
	      $('#python-log').hide();
	      $('#left-area .overlay').show();
	
	      $.ajax({
	        type: "POST",
	        url: location.pathname + '/run',
	        data: {
	          webdav_mode: _this.webdav_mode,
	          script: _this.webdav_mode ? '' : script,
	          task: task
	        },
	        success: function success(data) {
	          console.log(data);
	          $('#left-area .overlay').hide();
	
	          //web
	          $("#tab-web .iframe-box").html('<iframe sandbox="allow-same-origin allow-scripts" height="50%"></iframe>');
	          var iframe = $("#tab-web iframe")[0];
	          var content_type = data.fetch_result.headers && data.fetch_result.headers['Content-Type'] && data.fetch_result.headers['Content-Type'] || "text/plain";
	
	          //html
	          $("#tab-html pre").text(data.fetch_result.content);
	          $("#tab-html").data("format", true);
	
	          if (content_type.indexOf('application/json') == 0) {
	            try {
	              var content = JSON.parse(data.fetch_result.content);
	              content = JSON.stringify(content, null, '  ');
	              content = "<html><pre>" + content + "</pre></html>";
	              iframe.src = _this.render_html(content, data.fetch_result.url, true, true, false);
	            } catch (e) {
	              iframe.src = "data:,Content-Type:" + content_type + " parse error.";
	            }
	          } else if (content_type.indexOf("text/html") == 0) {
	            iframe.src = _this.render_html(data.fetch_result.content, data.fetch_result.url, true, true, false);
	            $("#tab-html").data("format", false);
	          } else if (content_type.indexOf("text") == 0) {
	            iframe.src = "data:" + content_type + "," + data.fetch_result.content;
	          } else if (data.fetch_result.dataurl) {
	            iframe.src = data.fetch_result.dataurl;
	          } else {
	            iframe.src = "data:,Content-Type:" + content_type;
	          }
	
	          //follows
	          $('#tab-follows').html('');
	          var elem = $("#tab-control li[data-id=tab-follows] .num");
	
	          var newtask_template = '<div class="newtask" data-task="__task__"><span class="task-callback">__callback__</span> &gt; <span class="task-url">__url__</span><div class="task-run"><i class="fa fa-play"></i></div><div class="task-more"> <i class="fa fa-ellipsis-h"></i> </div></div>';
	          if (data.follows.length > 0) {
	            elem.text(data.follows.length).show();
	            var all_content = "";
	            window.newtasks = {};
	            $.each(data.follows, function (i, task) {
	              var callback = task.process;
	              callback = callback && callback.callback || '__call__';
	              var content = newtask_template.replace('__callback__', callback);
	              content = content.replace('__url__', task.url || '<span class="error">no_url!</span>');
	              all_content += content.replace('__task__', i);
	              window.newtasks[i] = task;
	            });
	            $('#tab-follows').append(all_content);
	            _this.bind_follows();
	          } else {
	            elem.hide();
	          }
	
	          //messages
	          $('#tab-messages pre').html('');
	          if (data.messages.length > 0) {
	            $("#tab-control li[data-id=tab-messages] .num").text(data.messages.length).show();
	            var messages = JSON.stringify(data.messages, null, '  ');
	            CodeMirror.runMode(messages, 'application/json', $('#tab-messages pre')[0]);
	            $('#tab-messages')[0];
	          } else {
	            $("#tab-control li[data-id=tab-messages] .num").hide();
	          }
	
	          $("#tab-control li.active").click();
	
	          // logs
	          _this.python_log(data.logs);
	        },
	        error: function error(xhr, textStatus, errorThrown) {
	          console.log(xhr, textStatus, errorThrown);
	          _this.python_log('error: ' + textStatus);
	          $('#left-area .overlay').hide();
	        }
	      });
	    },
	
	    python_log: function python_log(text) {
	      if (text) {
	        $('#python-log pre').text(text);
	        $('#python-log pre, #python-log').show();
	        $('#python-log-show').height(0);
	      } else {
	        $('#python-log pre, #python-log').hide();
	      }
	    },
	
	    webdav_mode: false,
	    toggle_webdav_mode: function toggle_webdav_mode(button) {
	      if (!this.webdav_mode) {
	        if (this.not_saved) {
	          if (!confirm("You have not saved changes. Ignore changes and switch to WebDav mode.")) {
	            return;
	          }
	          this.not_saved = false;
	        }
	        this.python_editor_elem.hide();
	        this.splitter.trigger('fullsize', 'prev');
	        $(button).addClass('active');
	        this.webdav_mode = !this.webdav_mode;
	      } else {
	        // leaving webdav mode, reload script
	        var _this = this;
	        $.ajax({
	          type: "GET",
	          url: location.pathname + '/get',
	          success: function success(data) {
	            _this.splitter.trigger('init');
	            _this.python_editor_elem.show();
	            _this.python_editor.setValue(data.script);
	            _this.not_saved = false;
	            $(button).removeClass('active');
	            _this.webdav_mode = !_this.webdav_mode;
	          },
	          error: function error() {
	            alert('Loading script from database error. Script may out-of-date.');
	            _this.python_editor_elem.show();
	            _this.splitter.trigger('init');
	            $(button).removeClass('active');
	            _this.webdav_mode = !_this.webdav_mode;
	          }
	        });
	      }
	    }
	  };
	}();
	
	Debugger.init();

/***/ },
/* 1 */,
/* 2 */,
/* 3 */
/***/ function(module, exports) {

	// removed by extract-text-webpack-plugin

/***/ },
/* 4 */,
/* 5 */,
/* 6 */,
/* 7 */
/***/ function(module, exports) {

	'use strict';
	
	// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
	// Author: Binux<i@binux.me>
	//         http://binux.me
	// Created on 2014-02-23 01:35:35
	// from: https://github.com/jsbin/jsbin
	
	$.fn.splitter = function (_type) {
	  var $document = $(document),
	      $blocker = $('<div class="block"></div>'),
	      $body = $('body');
	  // blockiframe = $blocker.find('iframe')[0];
	
	  var splitterSettings = JSON.parse(localStorage.getItem('splitterSettings') || '[]');
	  return this.each(function () {
	    var $el = $(this),
	        $originalContainer = $(this),
	        guid = $.fn.splitter.guid++,
	        $parent = $el.parent(),
	        type = _type || 'x',
	        $prev = type === 'x' ? $el.prevAll(':visible:first') : $el.nextAll(':visible:first'),
	        $handle = $('<div class="resize"></div>'),
	        dragging = false,
	        width = $parent.width(),
	        parentOffset = $parent.offset(),
	        left = parentOffset.left,
	        top = parentOffset.top,
	        // usually zero :(
	    props = {
	      x: {
	        display: 'block',
	        currentPos: $parent.offset().left,
	        multiplier: 1,
	        cssProp: 'left',
	        otherCssProp: 'right',
	        size: $parent.width(),
	        sizeProp: 'width',
	        moveProp: 'pageX',
	        init: {
	          top: 0,
	          bottom: 0,
	          width: 8,
	          'margin-left': '-4px',
	          height: '100%',
	          left: 'auto',
	          right: 'auto',
	          opacity: 0,
	          position: 'absolute',
	          cursor: 'ew-resize',
	          // 'border-top': '0',
	          'border-left': '1px solid rgba(218, 218, 218, 0.5)',
	          'z-index': 99999
	        }
	      },
	      y: {
	        display: 'block',
	        currentPos: $parent.offset().top,
	        multiplier: -1,
	        size: $parent.height(),
	        cssProp: 'bottom',
	        otherCssProp: 'top',
	        sizeProp: 'height',
	        moveProp: 'pageY',
	        init: {
	          top: 'auto',
	          cursor: 'ns-resize',
	          bottom: 'auto',
	          height: 8,
	          width: '100%',
	          left: 0,
	          right: 0,
	          opacity: 0,
	          position: 'absolute',
	          border: 0,
	          // 'border-top': '1px solid rgba(218, 218, 218, 0.5)',
	          'z-index': 99999
	        }
	      }
	    },
	        refreshTimer = null,
	        settings = splitterSettings[guid] || {};
	
	    var tracker = {
	      down: { x: null, y: null },
	      delta: { x: null, y: null },
	      track: false,
	      timer: null
	    };
	    $handle.bind('mousedown', function (event) {
	      tracker.down.x = event.pageX;
	      tracker.down.y = event.pageY;
	      tracker.delta = { x: null, y: null };
	      tracker.target = $handle[type == 'x' ? 'height' : 'width']() * 0.25;
	    });
	
	    $document.bind('mousemove', function (event) {
	      if (dragging) {
	        tracker.delta.x = tracker.down.x - event.pageX;
	        tracker.delta.y = tracker.down.y - event.pageY;
	        clearTimeout(tracker.timer);
	        tracker.timer = setTimeout(function () {
	          tracker.down.x = event.pageX;
	          tracker.down.y = event.pageY;
	        }, 250);
	        //disable change to y
	        //var targetType = type == 'x' ? 'y' : 'x';
	        //if (Math.abs(tracker.delta[targetType]) > tracker.target) {
	        //$handle.trigger('change', targetType, event[props[targetType].moveProp]);
	        //tracker.down.x = event.pageX;
	        //tracker.down.y = event.pageY;
	        //}
	      }
	    });
	
	    function moveSplitter(pos) {
	      if (type === 'y') {
	        pos -= top;
	      }
	      var v = pos - props[type].currentPos,
	          split = 100 / props[type].size * v,
	          delta = (pos - settings[type]) * props[type].multiplier,
	          prevSize = $prev[props[type].sizeProp](),
	          elSize = $el[props[type].sizeProp]();
	
	      if (type === 'y') {
	        split = 100 - split;
	      }
	
	      // if prev panel is too small and delta is negative, block
	      if (prevSize < 100 && delta < 0) {
	        // ignore
	      } else if (elSize < 100 && delta > 0) {
	        // ignore
	      } else {
	        // allow sizing to happen
	        $el.css(props[type].cssProp, split + '%');
	        $prev.css(props[type].otherCssProp, 100 - split + '%');
	        var css = {};
	        css[props[type].cssProp] = split + '%';
	        $handle.css(css);
	        settings[type] = pos;
	        splitterSettings[guid] = settings;
	        localStorage.setItem('splitterSettings', JSON.stringify(splitterSettings));
	
	        // wait until animations have completed!
	        if (moveSplitter.timer) clearTimeout(moveSplitter.timer);
	        moveSplitter.timer = setTimeout(function () {
	          $document.trigger('sizeeditors');
	        }, 120);
	      }
	    }
	
	    function resetPrev() {
	      $prev = type === 'x' ? $handle.prevAll(':visible:first') : $handle.nextAll(':visible:first');
	    }
	
	    $document.bind('mouseup touchend', function () {
	      if (dragging) {
	        dragging = false;
	        $handle.trigger('resize-end');
	        $blocker.remove();
	        // $handle.css( 'opacity', '0');
	        $body.removeClass('dragging');
	      }
	    }).bind('mousemove touchmove', function (event) {
	      if (dragging) {
	        moveSplitter(event[props[type].moveProp] || event.originalEvent.touches[0][props[type].moveProp]);
	      }
	    });
	
	    $blocker.bind('mousemove touchmove', function (event) {
	      if (dragging) {
	        moveSplitter(event[props[type].moveProp] || event.originalEvent.touches[0][props[type].moveProp]);
	      }
	    });
	
	    $handle.bind('mousedown touchstart', function (e) {
	      dragging = true;
	      $handle.trigger('resize-start');
	      $body.append($blocker).addClass('dragging');
	      props[type].size = $parent[props[type].sizeProp]();
	      props[type].currentPos = 0; // is this really required then?
	
	      resetPrev();
	      e.preventDefault();
	    });
	
	    /*
	       .hover(function () {
	       $handle.css('opacity', '1');
	       }, function () {
	       if (!dragging) {
	       $handle.css('opacity', '0');
	       }
	       })
	       */
	
	    $handle.bind('fullsize', function (event, panel) {
	      if (panel === undefined) {
	        panel = 'prev';
	      }
	      var split = 0;
	      if (panel === 'prev') {
	        split = 100;
	      }
	      $el.css(props[type].cssProp, split + '%');
	      $prev.css(props[type].otherCssProp, 100 - split + '%');
	      $handle.hide();
	    });
	
	    $handle.bind('init', function (event, x) {
	      $handle.css(props[type].init);
	      props[type].size = $parent[props[type].sizeProp]();
	      resetPrev();
	
	      // can only be read at init
	      top = $parent.offset().top;
	
	      $blocker.css('cursor', type == 'x' ? 'ew-resize' : 'ns-resize');
	
	      if (type == 'y') {
	        $el.css('border-right', 0);
	        $prev.css('border-left', 0);
	        $prev.css('border-top', '2px solid #ccc');
	      } else {
	        // $el.css('border-right', '1px solid #ccc');
	        $el.css('border-top', 0);
	        // $prev.css('border-right', '2px solid #ccc');
	      }
	
	      if ($el.is(':hidden')) {
	        $handle.hide();
	      } else {
	        if ($prev.length) {
	          $el.css('border-' + props[type].cssProp, '1px solid #ccc');
	        } else {
	          $el.css('border-' + props[type].cssProp, '0');
	        }
	        moveSplitter(x !== undefined ? x : settings[type] || $el.offset()[props[type].cssProp]);
	      }
	    }); //.trigger('init', settings.x || $el.offset().left);
	
	    $handle.bind('change', function (event, toType, value) {
	      $el.css(props[type].cssProp, '0');
	      $prev.css(props[type].otherCssProp, '0');
	      $el.css('border-' + props[type].cssProp, '0');
	
	      if (toType === 'y') {
	        // 1. drop inside of a new div that encompases the elements
	        $el = $el.find('> *');
	        $handle.appendTo($prev);
	        $el.appendTo($prev);
	        $prev.css('height', '100%');
	        $originalContainer.hide();
	        $handle.css('margin-left', 0);
	        $handle.css('margin-top', 5);
	
	        $handle.addClass('vertical');
	
	        delete settings.x;
	
	        $originalContainer.nextAll(':visible:first').trigger('init');
	        // 2. change splitter to the right to point to new block div
	      } else {
	        $el = $prev;
	        $prev = $tmp;
	
	        $el.appendTo($originalContainer);
	        $handle.insertBefore($originalContainer);
	        $handle.removeClass('vertical');
	        $el.css('border-top', 0);
	        $el = $originalContainer;
	        $originalContainer.show();
	        $handle.css('margin-top', 0);
	        $handle.css('margin-left', -4);
	        delete settings.y;
	
	        setTimeout(function () {
	          $originalContainer.nextAll(':visible:first').trigger('init');
	        }, 0);
	      }
	
	      resetPrev();
	
	      type = toType;
	
	      // if (type == 'y') {
	      // FIXME $prev should check visible
	      var $tmp = $el;
	      $el = $prev;
	      $prev = $tmp;
	      // } else {
	
	      // }
	
	      $el.css(props[type].otherCssProp, '0');
	      $prev.css(props[type].cssProp, '0');
	      // TODO
	      // reset top/bottom positions
	      // reset left/right positions
	
	      if ($el.is(':visible')) {
	        // find all other handles and recalc their height
	        if (type === 'y') {
	          var otherhandles = $el.find('.resize');
	
	          otherhandles.each(function (i) {
	            // find the top of the
	            var $h = $(this);
	            if (this === $handle[0]) {
	              // ignore
	            } else {
	              // TODO change to real px :(
	              $h.trigger('init', 100 / (otherhandles - i - 1));
	            }
	          });
	        }
	        $handle.trigger('init', value || $el.offset()[props[type].cssProp] || props[type].size / 2);
	      }
	    });
	
	    $prev.css('width', 'auto');
	    $prev.css('height', 'auto');
	    $el.data('splitter', $handle);
	    $el.before($handle);
	
	    // if (settings.y) {
	    //   $handle.trigger('change', 'y');
	    // }
	  });
	};
	
	$.fn.splitter.guid = 0;

/***/ }
/******/ ]);
//# sourceMappingURL=debug.js.map