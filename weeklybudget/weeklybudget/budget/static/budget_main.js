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

var refresh_calendar_search_terms = function (search_terms_str) {
    calendar_search_terms = search_terms_str;
    $('#txt__calendar_search').autocomplete({ source: calendar_search_terms });
}

// Autonumeric config
//const autoNumericOptions = {
//    isCancellable : false
//};
//var currency_ = value => currency(value, { formatWithSymbol: true });