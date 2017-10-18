/**
  The number of milliseconds to ignore clicks on the *same*
  button, after a button *that was not ignored* was clicked. Used by
  `$(document).ready()`.

  Equal to <code>500</code>.
 */
var MILLS_TO_IGNORE_CLICKS = 500;

// images
var SRC__MOBILE_IMAGES = "{% static 'jquery.mobile.images-1.4.5' %}";

// other env vars
var userLanguage;

var ajaxErr = function(xhr,errmsg,err) {
    user_message('fail', errmsg);
//    $('#payment_detail').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + xhr.responseText +
//        " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
    console.error(xhr.status + ": " + xhr.responseText + " - " + errmsg); // provide a bit more info about the error to the console
}

var user_message = function (passfail, message) {
    user_message_text = message;
    if (passfail === 'pass') {
        $('#div__user_message').children('.result-message-text').text(message);
        $('#div__user_message')
            .addClass('result-message-box-success')
            .removeClass('result-message-box-failure')
            .show();
        $('#div__user_message').children('.ui-icon').addClass('ui-icon-circle-check');
    } else {
        $('#div__user_message').children('.result-message-text')
            .html('<strong>Error: </strong> ' + message);
        $('#div__user_message')
            .removeClass('result-message-box-success')
            .addClass('result-message-box-failure')
            .show();
        $('#div__user_message').children('.ui-icon').addClass('ui-icon-alert');
    }
}

jQuery.fn.reverse = [].reverse;

// Set up Cross Site Request Forgery protection
function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}
var csrftoken = $.cookie('csrftoken');
$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            console.info('Prepping csrf token');
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

