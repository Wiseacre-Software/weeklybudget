// Main javascript for budget pages

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