$(function () {
    $.MsgBox = {
        Alert: function (title, msg) {
            GenerateHtml("alert", title, msg);
            btnOk();  
            btnNo();
        },
        Confirm: function (title, msg, url, callback) {
            GenerateHtml("confirm", title, msg);
            btnOk(callback, url);
            btnNo(url);
        }
    }
    
    var GenerateHtml = function (type, title, msg) {
        var _html = "";
        _html += '<div id="mb_box"></div><div id="mb_con"><span id="mb_tit">' + title + '</span>';
        _html += '<a id="mb_ico">x</a><div id="mb_msg">' + msg + '</div><div id="mb_btnbox">';
        if (type == "alert") {
            
        }
        if (type == "confirm") {
            _html += '<input id="mb_btn_ok" type="button" value="Download 100" />';
            _html += '<input id="mb_btn_no" type="button" value="Download All" />';
        }
        _html += '</div></div>';
        
        $("body").append(_html); 
        
        GenerateCss();
    }

    
    var GenerateCss = function () {
        $("#mb_box").css({ width: '100%', height: '100%', zIndex: '99999', position: 'fixed',
            filter: 'Alpha(opacity=60)', backgroundColor: 'black', top: '0', left: '0', opacity: '0.6'
        });
        $("#mb_con").css({ zIndex: '999999', width: '400px', position: 'fixed',
            backgroundColor: 'White', borderRadius: '15px'
        });
        $("#mb_tit").css({ display: 'block', fontSize: '14px', color: '#444', padding: '10px 15px',
            backgroundColor: '#DDD', borderRadius: '15px 15px 0 0',
            borderBottom: '3px solid #009BFE', fontWeight: 'bold'
        });
        $("#mb_msg").css({ padding: '20px', lineHeight: '20px',
            borderBottom: '1px dashed #DDD', fontSize: '13px'
        });
        $("#mb_ico").css({ display: 'block', position: 'absolute', right: '10px', top: '9px',
            border: '1px solid Gray', width: '18px', height: '18px', textAlign: 'center',
            lineHeight: '16px', cursor: 'pointer', borderRadius: '12px', fontFamily: 'Times New Roman'
        });
        $("#mb_btnbox").css({ margin: '15px 0 10px 0', textAlign: 'center' });
        $("#mb_btn_ok,#mb_btn_no").css({ width: '110px', height: '30px', color: 'white', border: 'none' });
        $("#mb_btn_ok").css({ backgroundColor: '#168bbb' });
        $("#mb_btn_no").css({ backgroundColor: 'gray', marginLeft: '20px' });
        
        $("#mb_ico").hover(function () {
            $(this).css({ backgroundColor: 'Red', color: 'White' });
        }, function () {
            $(this).css({ backgroundColor: '#DDD', color: 'black' });
        });
        var _widht = document.documentElement.clientWidth;  
        var _height = document.documentElement.clientHeight; 
        var boxWidth = $("#mb_con").width();
        var boxHeight = $("#mb_con").height();
        
        $("#mb_con").css({ top: (_height - boxHeight) / 2 + "px", left: (_widht - boxWidth) / 2 + "px" });
    }
    
    var btnOk = function (callback,url) {
        $("#mb_btn_ok").click(function () {
        	window.location.href = url + "?limit=100";
        });
    }
    
    var btnNo = function (url) {
        $("#mb_btn_no").click(function () {
        	window.location.href = url;
        });
        $("#mb_ico").click(function () {
        	parent.location.reload();
        });
    }
});