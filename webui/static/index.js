// vim: set et sw=2 ts=2 sts=2 ff=unix fenc=utf8:
// Author: Binux<i@binux.me>
//         http://binux.me
// Created on 2014-03-02 17:53:23

$(function() {
  $(".project-group>span").editable({
    name: 'group',
    pk: function(e) {
      return $(this).parents('tr').data("name");
    },
    emptytext: '[group]',
    placement: 'right',
    url: "/update"
  });

  $(".project-status>span").editable({
    type: 'select',
    name: 'status',
    source: [
      {value: 'TODO', text: 'TODO'},
      {value: 'STOP', text: 'STOP'},
      {value: 'CHECKING', text: 'CHECKING'},
      {value: 'DEBUG', text: 'DEBUG'},
      {value: 'RUNNING', text: 'RUNNING'}
    ],
    pk: function(e) {
      return $(this).parents('tr').data("name");
    },
    emptytext: '[status]',
    placement: 'right',
    url: "/update",
    success: function(response, value) {
      $(this).removeClass('status-'+$(this).attr('data-value')).addClass('status-'+value).attr('data-value', value).attr('style', '');
    }
  });

  $(".project-rate>span").editable({
    name: 'rate',
    pk: function(e) {
      return $(this).parents('tr').data("name");
    },
    validate: function(value) {
      var s = value.split('/');
      if (s.length != 2)
        return "format error: rate/burst";
      if (!$.isNumeric(s[0]) || !$.isNumeric(s[1]))
        return "format error: rate/burst";
    },
    highlight: false,
    emptytext: '0/0',
    placement: 'right',
    url: "/update"
  });

  $('.project-create').on('click', function() {
    var result = prompt('Create new project:');
    if (result && result.search(/[^\w]/) == -1) {
      location.href = "/debug/"+result;
    } else {
      alert('project name not allowed!');
    }
  });
});
