// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-02-23 15:19:19

window.SelectorHelper = (function() {
  var helper = $('#css-selector-helper');

  function merge_name(p) {
    var features = p.features;
    var element_name = '';
    features.forEach(function(f) {
      if (f.selected)
        element_name += f.name;
    });
    if (element_name === '') {
      return p.tag;
    }
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
    return pattern.trim();
  }

  function selector_changed(path) {
    $("#tab-web iframe").get(0).contentWindow.postMessage({
      type: "heightlight",
      css_selector: merge_pattern(path),
    }, '*');
  }
  
  var current_path = null;
  function render_selector_helper(path) {
    helper.find('.element').remove();
    var elements = [];
    $.each(path, function(i, p) {
      var span = $('<span>').addClass('element').data('info', p);
      $('<span class="element-name">').text(p.name).appendTo(span);
      if (p.selected) span.addClass('selected');
      if (p.invalid) span.addClass('invalid');

      var ul = $('<ul>');
      $.each(p.features, function(i, f) {
        var li = $('<li>').text(f.name).data('feature', f);
        if (f.selected) li.addClass('selected');
        li.appendTo(ul);
        // feature on click
        li.on('click', function(ev) {
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

      span.on('mouseover', function(ev) {
        var xpath = [];
        $.each(path, function(i, _p) {
          xpath.push(_p.xpath);
          if (_p === p) {
            return false;
          }
        });
        $("#tab-web iframe")[0].contentWindow.postMessage({
          type: 'overlay',
          xpath: '/' + xpath.join('/'),
        }, '*');
      })
      // path on click
      span.on('click', function(ev) {
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
    init: function() {
      var _this = this;
      _this.clear();
      window.addEventListener("message", function(ev) {
        if (ev.data.type == "selector_helper_click") {
          console.log(ev.data.path);
          render_selector_helper(ev.data.path);
          current_path = ev.data.path;
        }
      });

      $("#J-enable-css-selector-helper").on('click', function() {
        _this.clear();
        $("#tab-web iframe")[0].contentWindow.postMessage({
          type: 'enable_css_selector_helper'
        }, '*');
        _this.enable();
      });

      $("#task-panel").on("scroll", function(ev) {
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
      input.on('focus', function(ev) {
        $(this).select();
      });
      helper.find('.copy-selector').on('click', function(ev) {
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
      helper.find('.add-to-editor').on('click', function(ev) {
        Debugger.python_editor_replace_selection(merge_pattern(current_path));
      });
    },
    clear: function() {
      current_path = null;
      helper.hide();
      helper.removeClass('fixed');
      tab_web.removeClass('fixed');
      helper.find('.element').remove();
    },
    enable: function() {
      helper.show();
      helper.find('.copy-selector-input').hide();
      if ($("#debug-tabs").position().top < 0) {
        helper.addClass('fixed');
        tab_web.addClass('fixed');
      } else {
        helper.removeClass('fixed');
        tab_web.removeClass('fixed');
      }
    },
  }
})();

window.Debugger = (function() {
  var tmp_div = $('<div>');
  function escape(text) {
    return tmp_div.text(text).html();
  }

  window.addEventListener("message", function(ev) {
    if (ev.data.type == "resize") {
      $("#tab-web iframe").height(ev.data.height+60);
    }
  });

  return {
    init: function() {
      //init resizer
      this.splitter = $(".debug-panel:not(:first)").splitter().data('splitter')
          .trigger('init')
          .on('resize-start', function() {
            $('#left-area .overlay').show();
          })
          .on('resize-end', function() {
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
    init_python_editor: function($el) {
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
      cm.on('focus', function() {
        $el.addClass("focus");
      });
      cm.on('blur', function() {
        $el.removeClass("focus");
      });
      cm.on('change', function() {
        _this.not_saved = true;
      });
      window.addEventListener('beforeunload', function(e) {
        if (_this.not_saved) {
          var returnValue = "You have not saved changes.";
          (e || window.event).returnValue = returnValue;
          return returnValue;
        }
      });
    },

    python_editor_replace_selection: function(content) {
      this.python_editor.getDoc().replaceSelection(content);
    },

    auto_format: function(cm) {
      var pos = cm.getCursor(true);
      CodeMirror.commands.selectAll(cm);
      cm.autoFormatRange(cm.getCursor(true), cm.getCursor(false));
      cm.setCursor(pos);
    },

    format_string: function(value, mode) {
      var div = document.createElement('div');
      var cm = CodeMirror(div, {
        value: value,
        mode: mode
      });
      this.auto_format(cm);
      return cm.getDoc().getValue();
    },

    init_task_editor: function($el) {
      var cm = this.task_editor = CodeMirror($el[0], {
        value: task_content,
        mode: "application/json",
        indentUnit: 2,
        lineWrapping: true,
        styleActiveLine: true
      });
      this.auto_format(cm);
      cm.getDoc().clearHistory();
      cm.on('focus', function() {
        $el.addClass("focus");
      });
      cm.on('blur', function() {
        $el.removeClass("focus");
      });
    },

    bind_debug_tabs: function() {
      var _this = this;
      $('#tab-control > li[data-id]').on('click', function() {
        $('#tab-control > li[data-id]').removeClass('active');
        var name = $(this).addClass('active').data('id');
        $('#debug-tabs .tab').hide();
        $('#debug-tabs #'+name).show();
      });
      $("#tab-control li[data-id=tab-html]").on('click', function() {
        if (!!!$("#tab-html").data("format")) {
          var html_styled = "";
          CodeMirror.runMode(_this.format_string($("#tab-html pre").text(), 'text/html'), 'text/html',
                             function(text, classname) {
                               if (classname)
                                 html_styled += '<span class="cm-'+classname+'">'+escape(text)+'</span>';
                               else
                                 html_styled += escape(text);
                             });
          $("#tab-html pre").html(html_styled);
          $("#tab-html").data("format", true);
        }
      });
    },

    bind_run: function() {
      var _this = this;
      $('#run-task-btn').on('click', function() {
        _this.run();
      });
      $('#undo-btn').on('click', function(ev) {
        _this.task_editor.execCommand('undo');
      });
      $('#redo-btn').on('click', function(ev) {
        _this.task_editor.execCommand('redo');
      });
    },

    bind_save: function() {
      var _this = this;
      $('#save-task-btn').on('click', function() {
        var script = _this.python_editor.getDoc().getValue();
        $('#right-area .overlay').show();
        $.ajax({
          type: "POST",
          url: location.pathname+'/save',
          data: {
            script: script
          },
          success: function(data) {
            console.log(data);
            _this.python_log('');
            _this.python_log("saved!");
            _this.not_saved = false;
            $('#right-area .overlay').hide();
          },
          error: function(xhr, textStatus, errorThrown) {
            console.log(xhr, textStatus, errorThrown);
            _this.python_log("save error!\n"+xhr.responseText);
            $('#right-area .overlay').hide();
          }
        });
      });
    },

    bind_follows: function() {
      var _this = this;
      $('.newtask').on('click', function() {
        if ($(this).next().hasClass("task-show")) {
          $(this).next().remove();
          return;
        }
        var task = $(this).after('<div class="task-show"><pre class="cm-s-default"></pre></div>').data("task");
        task = JSON.stringify(window.newtasks[task], null, '  ');
        CodeMirror.runMode(task, 'application/json', $(this).next().find('pre')[0]);
      });
      
      $('.newtask .task-run').on('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        var task = $(this).parents('.newtask').data("task");
        task = JSON.stringify(window.newtasks[task], null, '  ');
        _this.task_editor.setValue(task);
        _this.run();
      });
    },

    bind_others: function() {
      var _this = this;
      $('#python-log-show').on('click', function() {
        if ($('#python-log pre').is(":visible")) {
          $('#python-log pre').hide();
          $(this).height(8);
        } else {
          $('#python-log pre').show();
          $(this).height(0);
        }
      });
      $('.webdav-btn').on('click', function() {
        _this.toggle_webdav_mode(this);
      })
    },

    render_html: function(html, base_url, block_script, resizer, selector_helper) {
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
        $(dom).find('body').append('<script src="'+location.protocol+'//'+location.host+'/helper.js">');
      }
      if (selector_helper) {
        $(dom).find('body').append('<script src="'+location.protocol+'//'+location.host+'/static/css_selector_helper.js">');
      }
      $(dom).find('base').remove();
      $(dom).find('head').append('<base>');
      $(dom).find('base').attr('href', base_url);
      $(dom).find('link[href]').each(function(i, e) {
        e = $(e);
        try {
          e.attr('href', URI(e.attr('href')).absoluteTo(base_url).toString());
        } catch (error) {
          console.log(error);
        }
      });
      $(dom).find('img[____src____]').each(function(i, e) {
        e = $(e);
        try {
          e.attr('____src____', URI(e.attr('____src____')).absoluteTo(base_url).toString());
        } catch (error) {
          console.log(error);
        }
      });
      html = dom.innerHTML;
      html = html.replace(/(\s)____src____=/g, "$1src=");
      return encodeURI("data:text/html;charset=utf-8,"+html);
    },

    run: function() {
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
        url: location.pathname+'/run',
        data: {
          webdav_mode: _this.webdav_mode,
          script: _this.webdav_mode ? '' : script,
          task: task
        },
        success: function(data) {
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
              content = "<html><pre>"+content+"</pre></html>";
              iframe.src = _this.render_html(content,
                                             data.fetch_result.url, true, true, false);
            } catch (e) {
              iframe.src = "data:,Content-Type:"+content_type+" parse error.";
            }
          } else if (content_type.indexOf("text/html") == 0) {
            iframe.src = _this.render_html(data.fetch_result.content,
                                           data.fetch_result.url, true, true, false);
            $("#tab-html").data("format", false);
          } else if (content_type.indexOf("text") == 0) {
            iframe.src = "data:"+content_type+","+data.fetch_result.content;
          } else if (data.fetch_result.dataurl) {
            iframe.src = data.fetch_result.dataurl
          } else {
            iframe.src = "data:,Content-Type:"+content_type;
          }

          //follows
          $('#tab-follows').html('');
          var elem = $("#tab-control li[data-id=tab-follows] .num");

          var newtask_template = '<div class="newtask" data-task="__task__"><span class="task-callback">__callback__</span> &gt; <span class="task-url">__url__</span><div class="task-run"><i class="fa fa-play"></i></div><div class="task-more"> <i class="fa fa-ellipsis-h"></i> </div></div>';
          if (data.follows.length > 0) {
            elem.text(data.follows.length).show();
            var all_content = "";
            window.newtasks = {};
            $.each(data.follows, function(i, task) {
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
            $('#tab-messages')[0]
          } else {
            $("#tab-control li[data-id=tab-messages] .num").hide();
          }

          $("#tab-control li.active").click();

          // logs
          _this.python_log(data.logs);
        },
        error: function(xhr, textStatus, errorThrown) {
          console.log(xhr, textStatus, errorThrown);
          _this.python_log('error: '+textStatus);
          $('#left-area .overlay').hide();
        }
      });
    },

    python_log: function(text) {
      if (text) {
        $('#python-log pre').text(text);
        $('#python-log pre, #python-log').show();
        $('#python-log-show').height(0);
      } else {
        $('#python-log pre, #python-log').hide();
      }
    },

    webdav_mode: false,
    toggle_webdav_mode: function(button) {
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
          success: function (data) {
            _this.splitter.trigger('init');
            _this.python_editor_elem.show();
            _this.python_editor.setValue(data.script);
            _this.not_saved = false;
            $(button).removeClass('active');
            _this.webdav_mode = !_this.webdav_mode;
          },
          error: function() {
            alert('Loading script from database error. Script may out-of-date.');
            _this.python_editor_elem.show();
            _this.splitter.trigger('init');
            $(button).removeClass('active');
            _this.webdav_mode = !_this.webdav_mode;
          },
        });
      }
    },
  };
})();

Debugger.init();
