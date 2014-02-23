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
  },

  init_python_editor: function($el) {
    var cm = this.python_editor = CodeMirror($el[0], {
      mode: "python",
      indentUnit: 4,
      lineWrapping: true,
      styleActiveLine: true,
      autofocus: true,
    });
    cm.on('focus', function() {
      $el.addClass("focus");
    });
    cm.on('blur', function() {
      $el.removeClass("focus");
    });
  },

  init_task_editor: function($el) {
    var cm = this.task_editor = CodeMirror($el[0], {
      mode: "application/json",
      indentUnit: 2,
      lineWrapping: true,
      styleActiveLine: true,
    });
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
}

Debugger.init();
