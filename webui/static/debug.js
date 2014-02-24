// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-02-23 15:19:19

var Debugger = {
  init: function() {
    //init resizer
    $(".debug-panel:not(:first)").splitter().data('splitter').trigger('init');

    //codemirror
    CodeMirror.keyMap.basic.Tab = 'indentMore';
    this.init_python_editor($("#python-editor"));
    this.init_task_editor($("#task-editor"));
    this.bind_debug_tabs();
    this.bind_run();
  },

  init_python_editor: function($el) {
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
  },

  auto_format: function(cm) {
    var pos = cm.getCursor(true);
    CodeMirror.commands.selectAll(cm);
    cm.autoFormatRange(cm.getCursor(true), cm.getCursor(false));
    cm.setCursor(pos);
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
    cm.on('focus', function() {
      $el.addClass("focus");
    });
    cm.on('blur', function() {
      $el.removeClass("focus");
    });
  },

  bind_debug_tabs: function() {
    $('#tab-control > li').on('click', function() {
      $('#tab-control > li').removeClass('active');
      var name = $(this).addClass('active').data('id');
      $('#debug-tabs .tab').hide();
      $('#debug-tabs #'+name).show();
    });
  },

  bind_run: function() {
    var _this = this;
    $('#run-task-btn').on('click', function() {
      _this.run();
    });
  },

  run: function() {
    var script = this.python_editor.getDoc().getValue();
    var task = this.task_editor.getDoc().getValue();
    var _this = this;

    $.ajax({
      type: "POST",
      url: location.pathname+'/run',
      data: {
        script: script,
        task: task
      },
      success: function(data) {
        console.log(data);

        //web
        $("#tab-web").html('<iframe sandbox="allow-same-origin allow-scripts"></iframe>');
        var elem = $("#tab-web iframe");
        var doc = elem[0].contentWindow.document;
        doc.open();
        doc.write(data.fetch_result.content);
        var dotime = 0, cnt=10;
        elem[0].contentWindow.addEventListener('resize', function() {
          setTimeout(function() {
            var now = (new Date()).getTime();
            if (now > dotime && cnt > 0 && $("#tab-web iframe").height() < doc.body.scrollHeight+20) {
              $("#tab-web iframe").height(doc.body.scrollHeight+20);
              cnt--;
            }
          }, 100);
          dotime = (new Date()).getTime() + 100;
        });
        window.doc = doc;
        doc.close();
        $("#tab-control li[data-id=tab-web]").click();

        //html
        var div = document.createElement('div');
        var cm = CodeMirror(div, {
          value: data.fetch_result.content,
          mode: "text/html"
        });
        _this.auto_format(cm);
        var formated_content = cm.getDoc().getValue();
        CodeMirror.runMode(formated_content, 'text/html', $("#tab-html pre")[0]);

        //follows
        elem = $("#tab-control li[data-id=tab-follows] .num");
        if (data.follows.length > 0)
          elem.text(data.follows.length).show();
        else
          elem.hide();
      },
      error: function(xhr, textStatus, errorThrown) {
        console.log(xhr, textStatus, errorThrown);
      }
    });
  }
};

Debugger.init();
