var account_type_list = [['debit', 'Debit'],
            ['credit', 'Credit'],
            ['virtual', 'Virtual']]

var bank_account_currently_editing = false;

function initBankAccountView() {
    // initialise UI
    var bank_account_balance_total = 0;
    var bank_account_count = 0;
    bank_account_currently_editing = false;

    $('.table__bank_account').DataTable( {
        rowReorder: { dataSrc: 'display_order' },
        ordering: false,
        paging: false,
        searching: false,
        info: false,
        fixedHeader: true,
        columns: [
            { },
            { data: 'display_order', visible: false, },
            { data: 'title' },
            { data: 'current_balance', className: 'money' },
            {
                render: function ( data, type, row ) {
                    var render_html = '<div class="account__min_balance_amount money"></div>';
                    render_html += '<div class="account__min_balance_date"></div>';
                    return (render_html);
                }
            },    // Min Balance will be populated after calendar refresh
            { className: 'dt-center' }
        ],
        columnDefs: [
            { targets: 'hide-in-compact', visible: true },
        ],
        drawCallback: bankAccountLoadComplete

    } )
    .on( 'row-reordered', function ( e, diff, edit ) {
        // Find the top-most row to be updated
        if (diff.length > 0) {
            var firstNode = 0;
            for ( var i=1, ien=diff.length ; i<ien ; i++ ) {
//                console.debug('tbl.on(row-reordered) [' + i + ']:- title: ' +  $(diff[i].node).find('.td__bank_account_title').text() + ', newData: ' +  diff[i].newData + ', oldData: ' + diff[i].oldData);
                if ( diff[i].oldData < firstNode.oldData ) firstNode = i;
            }
            updateAccount( $(diff[firstNode].node).find('td:first-child'), 'display_order', diff[firstNode].newData );
            loadBankAccounts();
        }

    } );

    $('.button__delete_account')
        .button( {
            icons: { primary: 'ui-icon-trash', secondary: null },
            text: false
        })
        .click(_.debounce(updateAccount, MILLS_TO_IGNORE_CLICKS, true));

    $('#btn__new_debit_account').button( { icons: { primary: 'ui-icon-plus', secondary: null }, text: false })
        .click(_.debounce(function () {
            addAccount({ action: 'new', account_type: 'debit' });
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#btn__new_credit_account').button( { icons: { primary: 'ui-icon-plus', secondary: null }, text: false })
        .click(_.debounce(function () {
            addAccount({ action: 'new', account_type: 'credit' });
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#btn__new_virtual_account').button( { icons: { primary: 'ui-icon-plus', secondary: null }, text: false })
        .click(_.debounce(function () {
            addAccount({ action: 'new', account_type: 'virtual' });
        }, MILLS_TO_IGNORE_CLICKS, true));

//    new AutoNumeric.multiple('.td__bank_account_balance');
//    $('td__bank_account_balance').autoNumeric('init', {currencySymbol: '$'} );
    $('.td__bank_account_balance')
        .click(showEditBankBalanceField)
        .each(function() {
            bank_account_balance_total += parseFloat($(this).get());
            bank_account_count++;
        })
        .on("blur enterKey", "input", function (event) {    // delegated event for edit fields
            $(this).off("blur enterKey");
            $(this).parents('tr').data('bank_account_balance', $(this).autoNumeric('get')); //getNumericString
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

    updateBankAccountAfterCalendarRefresh();
}

var bankAccountLoadComplete = function( settings, json ) {
    $('.table__bank_account td.money').autoNumeric('init', {currencySymbol: '$'} );
    $('.account__min_balance_amount').autoNumeric('init', {currencySymbol: '$'} );
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
                    var v = self.autoNumeric('get'); //getNumericString
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
    var currVal = $this.autoNumeric('get'); //getNumericString
    $this.empty().append('<input type="text" value="' + currVal + '">');
    $this.off("click");
    $this.children('input').first().autoNumeric('init', {currencySymbol: '$'}).select();
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

var updateAccount = function(el, update_field, new_position){
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
        case 'display_order':
            payload.display_order = new_position;
            break;
    }
//    console.debug("updateAccount:- payload: " + jQuery.param(payload));
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

var updateBankAccountAfterCalendarRefresh = function() {
    // TODO check for race conditions between calendar and bank account loads
    if (typeof bank_balance__min === 'undefined' || bank_balance__min === 'None' || bank_balance__min === ''
        || $('.td__bank_account_balance_min').length === 0)
        return;

    $('.td__bank_account_balance_min').each(function() {
        if ($(this).parent().data('bank_account_title') in bank_balance__min) {
            var bank_balance__min_obj = bank_balance__min[$(this).parent().data('bank_account_title')];
            $(this).children('.account__min_balance_amount').autoNumeric('set', bank_balance__min_obj['amount']);
            $(this).children('.account__min_balance_date').text(moment(bank_balance__min_obj['payment_date']).format('L'));
            if ($(this).children('.account__min_balance_amount').autoNumeric('get') < 0) {
                $(this).addClass('result-message-box-failure');
            } else {
                $(this).removeClass('result-message-box-failure');
            }
        }
    });
}
