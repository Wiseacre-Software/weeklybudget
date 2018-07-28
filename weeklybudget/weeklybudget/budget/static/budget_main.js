// Main javascript for budget pages
var categorymap;
var user_message_text;

$.widget( "ui.checkboxradio", $.ui.checkboxradio, {
    refresh: function() {
        var checked = this.element[ 0 ].checked,
			isDisabled = this.element[ 0 ].disabled;

		this._updateIcon( checked );
		this._toggleClass( this.label, "ui-checkboxradio-checked", "ui-state-active", checked );
//		if ( this.options.label !== null ) {
//			this._updateLabel();
//		}

		if ( isDisabled !== this.options.disabled ) {
			this._setOptions( { "disabled": isDisabled } );
		}
    }
});

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

var refresh_calendar_search_terms = function (search_terms_str) {
    calendar_search_terms = search_terms_str;
    $('#txt__calendar_search').autocomplete({ source: calendar_search_terms });
}
