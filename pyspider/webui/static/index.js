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

  $('.project-run').on('click', function() {
    var project = $(this).parents('tr').data("name");
    var status = $(this).parents('tr').find(".project-status [data-value]").data("value");

    $("#need-set-status-alert").hide();
    if (status != "RUNNING" && status != "DEBUG") {
      $("#need-set-status-alert").show();
    }
    
    var _this = this;
    $(this).addClass("btn-warning");
    $.ajax({
      type: "POST",
      url: '/run',
      data: {
        project: project
      },
      success: function(data) {
        console.log(data);
        $(_this).removeClass("btn-warning");
        if (!data.result) {
          $(_this).addClass("btn-danger");
        }
      },
      error: function() {
        $(_this).removeClass("btn-warning").addClass("btn-danger");
      }
    });
  });

  //$("input[name=start-urls]").on('keydown', function(ev) {
    //if (ev.keyCode == 13) {
      //var value = $(this).val();
      //var textarea = $('<textarea class="form-control" rows=3 name="start-urls"></textarea>').replaceAll(this);
      //textarea.val(value).focus();
    //}
  //});

  $("#create-project-modal form").on('submit', function(ev) {
    var $this = $(this);
    var project_name = $this.find('[name=project-name]').val()
    if (project_name.length == 0 || project_name.search(/[^\w]/) != -1) {
      $this.find('[name=project-name]').parents('.form-group').addClass('has-error');
      $this.find('[name=project-name] ~ .help-block').show();
      return false;
    }
    var mode = $this.find('[name=script-mode]:checked').val();
    $this.attr('action', '/debug/'+project_name);
    return true;
  });

  // onload
  function fill_progress(project, type, info) {
    var $e = $("tr[data-name="+project+"] td.progress-"+type);

    if (!!!info) {
      $e.attr("title", "");
      $e.attr('data-value', 0);
      $e.find(".progress-text").text(type);
      $e.find(".progress-pending").width("0%");
      $e.find(".progress-success").width("0%");
      $e.find(".progress-retry").width("0%");
      $e.find(".progress-failed").width("0%");
      return ;
    }

    var pending = info.pending || 0,
    success = info.success || 0,
    retry = info.retry || 0,
    failed = info.failed || 0,
    sum = info.task || pending + success + retry + failed;
    $e.attr("title", ""+type+" of "+sum+" tasks:\n"
            +(type == "all"
              ? "pending("+(pending/sum*100).toFixed(1)+"%): \t"+pending+"\n"
              : "new("+(pending/sum*100).toFixed(1)+"%): \t\t"+pending+"\n")
              +"success("+(success/sum*100).toFixed(1)+"%): \t"+success+"\n"
              +"retry("+(retry/sum*100).toFixed(1)+"%): \t"+retry+"\n"
              +"failed("+(failed/sum*100).toFixed(1)+"%): \t"+failed
           );
           $e.attr('data-value', sum);
           $e.find(".progress-text").text(type+": "+sum);
           $e.find(".progress-pending").width(""+(pending/sum*100)+"%");
           $e.find(".progress-success").width(""+(success/sum*100)+"%");
           $e.find(".progress-retry").width(""+(retry/sum*100)+"%");
           $e.find(".progress-failed").width(""+(failed/sum*100)+"%");
  }
  function update_counters() {
    $.get('/counter', function(data) {
      //console.log(data);
      $('tr[data-name]').each(function(i, tr) {
        var project = $(tr).data('name');
        var info = data[project];
        if (info === undefined) {
          return ;
        }

        if (info['5m_time']) {
          var fetch_time = (info['5m_time']['fetch_time'] || 0) * 1000;
          var process_time = (info['5m_time']['process_time'] || 0) * 1000;
          $(tr).find('.project-time').attr('data-value', fetch_time+process_time).text(
            ''+fetch_time.toFixed(1)+'+'+process_time.toFixed(2)+'ms');
        } else {
          $(tr).find('.project-time').attr('data-value', '').text('');
        }

        fill_progress(project, '5m', info['5m']);
        fill_progress(project, '1h', info['1h']);
        fill_progress(project, '1d', info['1d']);
        fill_progress(project, 'all', info['all']);
      });
    });
  }
  window.setInterval(update_counters, 15*1000);
  update_counters();

  function update_queues() {
    $.get('/queues', function(data) {
      //console.log(data);
      $('.queue_value').each(function(i, e) {
        var attr = $(e).attr('title');
        if (data[attr] !== undefined) {
          $(e).text(data[attr]);
        } else {
          $(e).text('???');
        }
      });
    });
  }
  window.setInterval(update_queues, 15*1000);
  update_queues();

  // table sortable
  Sortable.getColumnType = function(table, i) {
    var type = $($(table).find('th').get(i)).data('type');
    if (type == "num") {
      return Sortable.types.numeric;
    } else if (type == "date") {
      return Sortable.types.date;
    }
    return Sortable.types.alpha;
  };
  $('table.projects').attr('data-sortable', true);
  Sortable.init();
});
