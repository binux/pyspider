// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-02-23 15:19:19


window.Debugger = (function() {
  var tmp_div = $('<div>');
  function escape(text) {
    return tmp_div.text(text).html();
  }

  window.addEventListener("message", function(ev) {
    if (ev.data.type == "resize") {
      $("#tab-web iframe").height(ev.data.height+60);
    } else if (ev.data.type == "selector") {
      Debugger.python_editor.getDoc().replaceSelection(ev.data.selector);
    }
  });

  return {
    init: function() {
      //init resizer
      $(".debug-panel:not(:first)").splitter().data('splitter')
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
    },

    not_saved: false,
    init_python_editor: function($el) {
      var _this = this;
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
      $("#enable_css_selector_helper").on('click', function() {
        var iframe = $("#tab-web iframe")[0];
        iframe.contentWindow.postMessage({type: 'enable_css_selector_helper'}, '*');
        Debugger.python_editor.getDoc().replaceSelection('');
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
      $('#python-log-show').on('click', function() {
        if ($('#python-log pre').is(":visible")) {
          $('#python-log pre').hide();
          $(this).height(8);
        } else {
          $('#python-log pre').show();
          $(this).height(0);
        }
      });
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
        $(dom).find('body').append('<script src="http://'+location.host+'/helper.js">');
      }
      if (selector_helper) {
        $(dom).find('body').append('<script src="http://'+location.host+'/static/css_selector_helper.js">');
      }
      $(dom).find('base').remove();
      $(dom).find('head').append('<base>');
      $(dom).find('base').attr('href', base_url);
      $(dom).find('link[href]').each(function(i, e) {
        e = $(e);
        e.attr('href', URI(e.attr('href')).absoluteTo(base_url).toString());
      });
      $(dom).find('img[____src____]').each(function(i, e) {
        e = $(e);
        e.attr('____src____', URI(e.attr('____src____')).absoluteTo(base_url).toString());
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
      $("#tab-web").html('<iframe sandbox></iframe>');
      $("#tab-html pre").html('');
      $('#tab-follows').html('');
      $("#tab-control li[data-id=tab-follows] .num").hide();
      $('#python-log').hide();
      $('#left-area .overlay').show();

      $.ajax({
        type: "POST",
        url: location.pathname+'/run',
        data: {
          script: script,
          task: task
        },
        success: function(data) {
          console.log(data);
          $('#left-area .overlay').hide();

          //web
          $("#tab-web").html('<iframe sandbox="allow-same-origin allow-scripts" height="50%"></iframe>');
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
    }
  };
})();

Debugger.init();
