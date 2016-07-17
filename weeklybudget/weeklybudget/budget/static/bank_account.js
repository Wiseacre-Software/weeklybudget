function initBankAccountView() {
    // initialise UI
    var bank_account_balance_total = 0;
    var bank_account_count = 0;
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
            updateAccount( $(this) );
        })
        .on("keyup", "input", (function(e){
            if(e.keyCode == 13)
            {
                $(this).trigger("enterKey");
            }
        }));

    $('.td__bank_account_title')
        .click(showEditBankTitleField)
        .on("blur enterKey", "input", function (event) {    // delegated event for edit fields
            $(this).off("blur enterKey");
            $(this).parents('tr').data('bank_account_title', $(this).val());
            updateAccount( $(this) );
        })
        .on("keyup", "input", (function(e){
            if(e.keyCode == 13)
            {
                $(this).trigger("enterKey");
            }
        }));

    if (bank_account_count > 1) {
        $('.td__bank_account_total_balance')
            .text(bank_account_balance_total)
            .autoNumeric('init', {aSign: '$'});
    } else {
        $('.td__bank_account_total_balance').closest('tfoot').hide();
    }

    $('#href__add_account')
        .button()
        .click(function() {
            payload = { 'action' : 'blank' };
            addAccount(payload);
        });

    // datatable
    $('#table__accounts').DataTable({
        "ordering": false,
        "searching": false,
        "paging": false,
        "info": false
//        "footerCallback": function ( row, data, start, end, display ) {
//            if (data.length > 1) {
//                var api = this.api(), data;
//
//                // Remove the formatting to get integer data for summation
//                var floatVal = function ( i ) {
//                    return typeof i === 'string' ?
//                        i.replace(/[\$,]/g, '')*1.0 :
//                        typeof i === 'number' ?
//                            i : 0.0;
//                };
//
//                // Total over all pages
//                total = api
//                    .column( 1 )
//                    .data()
//                    .reduce( function (a, b) {
//                        return floatVal(a) + floatVal(b);
//                    }, 0 );
//
//                // Update footer
//                var numFormat = $.fn.dataTable.render.number( '\,', '.', 2, '$' ).display;
//                $( api.column( 1 ).footer() ).html(numFormat(total));
//            }
//        }
    });

}

function loadBankAccounts() {
    var config = {
        type: "GET",
        url: URL__BANK_ACCOUNT_VIEW,
        dataType: 'html',
        data: { 'action': 'blank' },
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
                $('#span_add_account_form').html(serverResponse_data);

                // init UI
                var bank_account_title_default = 'Bank Account #1';
                var bank_account_balance_default = 'Current Balance';

                $('.bank_account_title')
                    .prop('defaultValue', bank_account_title_default)
                    .blur( function () {
                        if( !$(this).val().trim() ) {
                            $(this).val(bank_account_title_default);
                        }
                    });

                $('.bank_account_balance').autoNumeric('init', {aSign: '$'})
                    .prop('defaultValue',bank_account_balance_default)
                    .prop('value',bank_account_balance_default)
                    .blur( function () {
                        if( !$(this).val().trim() ) {
                            $(this).val(bank_account_balance_default);
                        }
                    }).focus( function() {
                        if( $(this).val().trim() == bank_account_balance_default ) {
                            $(this).val('');
                        }
                    });

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
    var $this = $(this);
    var currVal = $this.autoNumeric('get');
    $this.empty().append('<input type="text" value="' + currVal + '">');
    $this.off("click")
    $this.children('input').first().autoNumeric('init', {aSign: '$'});
}

var showEditBankTitleField = function() {
    var $this = $(this);
    var currVal = $this.text();
    $this.empty().append('<input type="text" class="ui-widget" value="' + currVal + '">');
    $this.off("click")
}

var updateAccount = function(el){
    payload = {
        'action' : 'update',
        'bank_account_id' : el.closest('tr').data('bank_account_id'),
        'title' : el.closest('tr').data('bank_account_title'),
        'current_balance' : el.closest('tr').data('bank_account_balance')
    };

    console.info("updateAccount: entering, payload: " + jQuery.param(payload));

    var jqxhr = $.ajax({
            method: "POST",
            url: URL__BANK_ACCOUNT_VIEW,
            data: jQuery.param(payload)
        })
        .done(function(serverResponse_data) {
            try {
                var o = JSON.parse(serverResponse_data);
                console.warn("updateAccount:- serverResponse_data: " + serverResponse_data);
            } catch (e) {
                $('#div__accounts').html(serverResponse_data);
            }
        })
        .fail(ajaxErr);
}