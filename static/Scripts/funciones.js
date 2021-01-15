//CSRF Protection
$(document).ajaxSend(function(event, xhr, settings) {
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    function sameOrigin(url) {
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }
    function safeMethod(method) {
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }

    if (!safeMethod(settings.type) && sameOrigin(settings.url)) {
        xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
});

Array.prototype.Contains = function(v) {
    for(var i = 0; i < this.length; i++) {
        if(this[i] === v) return true;
    }
    return false;
};

if (!String.prototype.format) {
    String.prototype.format = function () {
        var args = arguments;
        var new_string = this;
        for (var i=0; i < args.length; i++) {
            new_string = new_string.replace('{' + i.toString() + '}', args[i]);
        }
        return new_string;
    };
}

if (!String.prototype.join) {
    String.prototype.join = function (list) {
        var new_string = '';
        var separator = this.toString();
        for (value of list) {
            new_string += value.toString() + separator;
        }
        return new_string;
    };
}

function _notify(ms, from, align, icon, type, animIn, animOut, timer){
    $.growl({
        icon: icon,
        title: ' Notificación ',
        message: ms,
        url: ''
    },{
        element: 'body',
        type: type,
        allow_dismiss: true,
        placement: {
                from: from,
                align: align
        },
        offset: {
            x: 20,
            y: 85
        },
        spacing: 10,
        z_index: 1031,
        delay: 2500,
        timer: timer,
        url_target: '_blank',
        mouse_over: false,
        animate: {
            enter: animIn,
            exit: animOut
        },
        icon_type: 'class',
        template: '<div data-growl="container" class="alert" role="alert">' +
                        '<button type="button" class="close" data-growl="dismiss">' +
                            '<span aria-hidden="true">&times;</span>' +
                            '<span class="sr-only">Close</span>' +
                        '</button>' +
                        '<span data-growl="icon"></span>' +
                        '<span data-growl="title"></span>' +
                        '<span data-growl="message"></span>' +
                        '<a href="#" data-growl="url"></a>' +
                    '</div>'
    });
};


function notification(ms, code) {
    _notify(
        ms,
        undefined, undefined, undefined,
        code, 'animated bounceIn', '', 5000
    );
}

function success(ms) {
    notification(ms, 'success');
}

function warning(ms) {
    notification(ms, 'warning');
}

function danger(ms) {
    notification(ms, 'danger');
}

// Permite checkear todos los checkboxes de una tabla con el checkbox todos.
function checkTodos(idTabla){
	$("#"+idTabla+" input:checkbox").attr('checked', $("#"+idTabla+" .todos").is(':checked'));
}

// Permite agregar opciones a un select.
function agregarOpciones(data, idCombo){
	var opciones = '<option value="-1" selected="selected">------</option>';
	data.forEach(function(item){
		opciones += '<option value="' + item['pk'] + '">' + item['fields']['nombre'] + '</option>';
	});
	//$("#"+idCombo).empty();
    $("#"+idCombo).html(opciones);
    $("#"+idCombo).trigger('chosen:updated');
}

// Permite agregar opciones a un select.
function agregarOpciones2(data, idCombo){
    // var opciones = '<option value="-1" selected="selected">------</option>';
    var opciones = '';
    data.forEach(function(item){
        opciones += '<option value="' + item['pk'] + '">' + item['nombre'] + '</option>';
    });
    //$("#"+idCombo).empty();
    $("#"+idCombo).html(opciones);
    $("#"+idCombo).trigger('chosen:updated');
}
