var account_type_list = [['debit', 'Debit'],
            ['credit', 'Credit'],
            ['virtual', 'Virtual']]

var bank_account_currently_editing = false;

function initBankAccountView() {
    // initialise UI
    var bank_account_balance_total = 0;
    var bank_account_count = 0;
    bank_account_currently_editing = false;

    $('.td__bank_account_balance')
        .autoNumeric('init', {aSign: '$'})
        .click(showEditBankBalanceField)
        .each(function() {
            bank_account_balance_total += parseFloat($(this).autoNumeric('get'));
            bank_account_count++;
        })
        .on("blur enterKey", "input", function (event) {    // delegated event for edit fields
            $(this).off("blur enterKey");
            $(this).parents('tr').data('bank_account_balance', $(this).autoNumeric('get'));
            updateAccount( $(this), 'bank_account_balance' );
            loadBankAccounts();
            reloadCalendar();
        })
        .on("keyup", "input", (function(e){
            if(e.keyCode == 13) $(this).trigger("enterKey");
            if(e.keyCode == 27) loadBankAccounts(); // esc
        }));

    $('.td__bank_account_title')
        .click(showEditBankTitleField)
        .on("blur enterKey", "input", function (event) {    // delegated event for edit fields
            $(this).off("blur enterKey");
            $(this).parents('tr').data('bank_account_title', $(this).val());
            updateAccount( $(this), 'bank_account_title' );
            loadBankAccounts();
            reloadCalendar();
        })
        .on("keyup", "input", (function(e){
            if(e.keyCode == 13) $(this).trigger("enterKey");
            if(e.keyCode == 27) loadBankAccounts(); // esc
        }));

    $('.td__bank_account_type')
        .click(showEditBankAccountTypeField);

    $('#href__add_account')
        .button()
        .click(function() {
            payload = { 'action' : 'new' };
            addAccount(payload);
        });
}

function loadBankAccounts() {
    var config = {
        type: "GET",
        url: URL__BANK_ACCOUNT_VIEW,
        dataType: 'html',
//        data: { 'action': 'blank' },
        success: processLoadBankAccountsServerResponse,
        error: ajaxErr,
        cache: false
    };
    $.ajax(config);
}

var processLoadBankAccountsServerResponse = function(serverResponse_data, textStatus_ignored, jqXHR_ignored) {
    try {
        var o = JSON.parse(serverResponse_data);
        console.info("processLoadBankAccountsServerResponse:- serverResponse_data: " + serverResponse_data);
        $('.calendar_view').text(o['result']);
    } catch (e) {
//        console.log("processLoadBankAccountsServerResponse:- It's HTML")
        $('.bank_account_view').html(serverResponse_data);
    }
}

var addAccount = function (payload) {
    console.info("addAccount: entering, payload: " + payload);
    event.preventDefault();

    var jqxhr = $.ajax({
            method: "POST",
            url: URL__BANK_ACCOUNT_VIEW,
            data: payload
        })
        .done(function(serverResponse_data) {
            try {
                var o = JSON.parse(serverResponse_data);
                console.warn("addAccount:- serverResponse_data: " + serverResponse_data);
            } catch (e) {
                $('.bank_account_view').html(serverResponse_data);0

//                // init UI
//                var bank_account_title_default = 'Bank Account #1';
//                var bank_account_balance_default = 'Current Balance';
//
//                $('.bank_account_title')
//                    .prop('defaultValue', bank_account_title_default)
//                    .blur( function () {
//                        if( !$(this).val().trim() ) {
//                            $(this).val(bank_account_title_default);
//                        }
//                    });
//
//                $('.bank_account_balance').autoNumeric('init', {aSign: '$'})
//                    .prop('defaultValue',bank_account_balance_default)
//                    .prop('value',bank_account_balance_default)
//                    .blur( function () {
//                        if( !$(this).val().trim() ) {
//                            $(this).val(bank_account_balance_default);
//                        }
//                    }).focus( function() {
//                        if( $(this).val().trim() == bank_account_balance_default ) {
//                            $(this).val('');
//                        }
//                    });

            }
        })
        .fail(ajaxErr)
        .always(function() {
            console.info("addAccount: and we're back");
        });
}

function initBankAccountForm() {
    $('#form__bank_account_update input:submit').button();
    $("#form__bank_account_update").validate({
        rules: {
            title: { required: true },
            current_balance: {
                required: true,
                defaultInvalid: true
            },
            account_type: {
                required: true
            }
        },
        submitHandler: function() {
            // do any cleanup
            $('#form__bank_account_update.money').each(function(i){
                var self = $(this);
                try{
                    var v = self.autoNumeric('get');
                    self.autoNumeric('destroy');
                    self.val(v);
//                    console.log("Found autonumeric field: " + self.attr("name"));
                }catch(err){
//                    console.log("Not an autonumeric field: " + self.attr("name"));
                }
            });

            addAccount($('#form__bank_account_update').serialize());
        }
    });
 }

var showEditBankBalanceField = function() {
    if (bank_account_currently_editing) return false;
    bank_account_currently_editing = true;
    var $this = $(this);
    var currVal = $this.autoNumeric('get');
    $this.empty().append('<input type="text" value="' + currVal + '">');
    $this.off("click");
    $this.children('input').first().autoNumeric('init', {aSign: '$'}).select();
}

var showEditBankTitleField = function() {
    if (bank_account_currently_editing) return false;
    bank_account_currently_editing = true;
    var $this = $(this);
    var currVal = $this.text();
    $this.empty().append('<input type="text" class="ui-widget" value="' + currVal + '">');
    $this.find('input').select();
    $this.off("click");
}

var showEditBankAccountTypeField = function() {
    if (bank_account_currently_editing) return true;
    bank_account_currently_editing = true;
    var $this = $(this);
    var currVal = $this.text();
    var s = $('<select />', { class: 'cbo__edit_bank_account_type' });
    for (i=0; i < account_type_list.length; i++) {
        var a = account_type_list[i];
        $('<option />', {value: a[0], text: a[1]}).appendTo(s);
    }
    $div1 = $('<span />', { class: 'div__edit_bank_account_type_select'});
    s.appendTo($div1);
    $div2 = $('<span />', { class: 'div__edit_bank_account_type_buttons'});
    ($('<button />', { class: 'cbo__edit_bank_account_type_ok', text: 'OK' })).appendTo($div2);
    ($('<button />', { class: 'cbo__edit_bank_account_type_cancel', text: 'Cancel' })).appendTo($div2);
    $this.empty().append($div1).append($div2);
    $this.unbind('click');
    $('.cbo__edit_bank_account_type').chosen( { width: '80px' });
    $('.cbo__edit_bank_account_type_ok').button( {
            icons: { primary: 'ui-icon-check', secondary: null },
            text: false
        })
        .click(_.once(function() {
            $(this).parents('tr').data('bank_account_type', $('.cbo__edit_bank_account_type').chosen().val());
            updateAccount( $(this), 'bank_account_type' );
            loadBankAccounts();
            reloadCalendar();
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('.cbo__edit_bank_account_type_cancel').button( {
            icons: { primary: 'ui-icon-close', secondary: null },
            text: false
        })
        .click(_.once(loadBankAccounts, MILLS_TO_IGNORE_CLICKS, true));
}

var updateAccount = function(el, update_field){
    payload = {
        'action' : 'update',
        'bank_account_id' : el.closest('tr').data('bank_account_id')
    };
    switch(update_field) {
        case 'bank_account_title':
            payload.title = el.closest('tr').data('bank_account_title');
            break;
        case 'bank_account_balance':
            payload.current_balance = el.closest('tr').data('bank_account_balance');
            break;
        case 'bank_account_type':
            payload.account_type = el.closest('tr').data('bank_account_type');
            break;
    }
    var jqxhr = $.ajax({
            method: "POST",
            url: URL__BANK_ACCOUNT_VIEW,
            data: jQuery.param(payload)
        })
        .done(function(serverResponse_data) {
            try {
                var o = JSON.parse(serverResponse_data);
//                console.warn("updateAccount:- serverResponse_data: " + serverResponse_data);
            } catch (e) {
                $('#div__accounts').html(serverResponse_data);
            }
        })
        .fail(ajaxErr);
}