//THIS FILE MUST BE IMPORTED BEFORE THE "main" FILE.

function categoryMapLookup(searchtype, val) {
    var searchindex = 2;
    if (searchtype == 'payment_type') searchindex = 0;
    else if (searchtype == 'category') searchindex = 1;

    var res = [];
    for (i=0; i < categorymap.length; i++) {
        if (categorymap[i][searchindex] == val) {
            res = categorymap[i];
            break;
        }
    }

    return res
}

function initUpdatePayment() {
    // jquery-ui
//    $('#form__payment_detail input, #form__payment_detail label, #table__payment_detail td').addClass('ui-widget');
    $('#form__payment_detail button, #form__payment_detail input:submit').button();
    $("#id_next_date").datepicker({dateFormat: "dd/mm/yy"});
    $('#input__weekly_dow_frequency').spinner({min: 1});
    $("#span__weekly_dow_day").buttonset();
    $('#input__monthly_dom_frequency').spinner({min: 1});
    $('#input__monthly_wom_frequency').spinner({min: 1});
    $('#id_annual_frequency').attr('type', 'text').spinner({min: 1});

    var rgx = new RegExp('[^0-9.]');
    if (rgx.test($('input.money').val())) {
        $('input.money').val($('input.money').val().replace(/[^0-9.]/g, ''));   // clean up amount if necessary
        $('input.money').autoNumeric('init', {aSign: '$'});
        $('input.money').autoNumeric('set', $('input.money').val());
    } else {
        $('input.money').autoNumeric('init', {aSign: '$'});
    }

    // init gui
    if ($("#id_next_date").val() === '') {
        $("#id_next_date").val(moment(new Date()).format('DD/MM/YYYY'))
    }
    $('#id_in_out').chosen({width: "95%"});
    $('#id_schedule_frequency').chosen({width: "95%"});
    $('#select__monthly_dom_day').chosen({width: '75px'});
    $('#select__monthly_dom_last').attr('data-placeholder', " ")
        .chosen({width: '75px', allow_single_deselect: true});
    $('#select__monthly_wom_nth').chosen({width: '75px'});
    $('#select__monthly_wom_last').attr('data-placeholder', " ")
        .chosen({width: '75px', allow_single_deselect: true});
    $('#select__monthly_wom_day').chosen({width: '125px'});
    $('#id_annual_dom').chosen({width: "75px"});
    $('#id_annual_moy').chosen({width: "125px"});

    initialiseCombos();
    initialiseFrequencyDetails();

    // hook up events
    $('#button__manage_categories').click(_.debounce(function (event) {
        event.preventDefault();
        $(this).button("disable");
        processManageCategories();
    },MILLS_TO_IGNORE_CLICKS, true));
    $('#button__update_payment_save_changes').click( submit_payment_detail_form );
    $('#button__update_payment_cancel').click(function() {
        event.preventDefault();
        $( "#calendar__overlay" ).dialog( "close" );
    });

    $('#id_subcategory')
        .attr('data-placeholder', "None")
        .trigger("chosen:updated")
        .chosen({
                width: "95%",
                allow_single_deselect: true
            })
        .change(function () {
        // select correct category
            var c = categoryMapLookup('subcategory', $(this).val());
            $('#id_payment_type').val(c[0]);
            $('#id_category').val(c[1]);
            $('#id_payment_type').trigger("chosen:updated");
            $('#id_category').trigger("chosen:updated");
        });

    $('#id_category')
        .attr('data-placeholder', "None")
        .trigger("chosen:updated")
        .chosen({
                width: "95%",
                allow_single_deselect: true
            })
        .change(function () {
            // select correct category
            var c = categoryMapLookup('category', $(this).val());
            $('#id_payment_type').val(c[0]);
            $('#id_subcategory').val(c[2]);
            $('#id_payment_type').trigger("chosen:updated");
            $('#id_subcategory').trigger("chosen:updated");
        });
    $('#id_payment_type').chosen({width: "95%"})
        .attr('data-placeholder', "Select a Payment Type")
        .change(function () {
            // select correct category
            var c = categoryMapLookup('payment_type', $(this).val());
            $('#id_category').val(c[1]);
            $('#id_subcategory').val(c[2]);
            $('#id_category').trigger("chosen:updated");
            $('#id_subcategory').trigger("chosen:updated");
        });

    $('#id_next_date').change(function (event) {
        if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
            $('#select__monthly_dom_day').val($(this).datepicker('getDate').getDate());
            $('#select__monthly_dom_day').trigger("chosen:updated");

            $('#select__monthly_wom_nth').val(Math.ceil($(this).datepicker('getDate').getDate() / 7));
            $('#select__monthly_wom_nth').trigger("chosen:updated");
            $('#select__monthly_wom_day').val(($(this).datepicker('getDate').getDay() + 6) % 7);
            $('#select__monthly_wom_day').trigger("chosen:updated");

        } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
            $('#span__weekly_dow_day').find('input:checkbox').each(function() { $(this).prop('checked',false) });
            $('#id_weekly_dow_' + moment($(this).val(), 'DD/MM/YYYY').format('ddd').toLowerCase()).prop('checked',true);
            $("#span__weekly_dow_day").buttonset('refresh');

        } else if ($('.select__schedule_frequency option:selected').text() == "Annual") {
            $('#id_annual_dom').val($(this).datepicker('getDate').getDate());
            $('#id_annual_dom').trigger("chosen:updated");
            $('#id_annual_moy').val($(this).datepicker('getDate').getMonth() + 1);
            $('#id_annual_moy').trigger("chosen:updated");
        }
    });

    // for Add Payment functionality
    if ($('#id_title').val() === '') {
        $( "#button__update_payment_save_changes" ).button( "option", "label", "Add" );
        $('#id_category').val('0');
        $('#id_category').trigger("chosen:updated");
        $('#id_subcategory').val('0');
        $('#id_subcategory').trigger("chosen:updated");
    }

    // frequency fields
    $('.select__schedule_frequency').change(initialiseFrequencyDetails);

    $("#input__weekly_dow_frequency").on("spinstop", function( event, ui ) {
        if ($(this).val() == 1) {
            $('#label__weekly_dow_frequency').text('week');
        }
        else {
            $('#label__weekly_dow_frequency').text('weeks');
        }
    } );
    $('#input__monthly_dom_frequency').on("spinstop", function( event, ui ) {
        if ($(this).val() == 1) {
            $('#label__monthly_dom_frequency').text('month');
        }
        else {
            $('#label__monthly_dom_frequency').text('months');
        }
    });
    $('#input__monthly_wom_frequency').on("spinstop", function( event, ui ) {
        if ($(this).val() == 1) {
            $('#label__monthly_wom_frequency').text('month');
        }
        else {
            $('#label__monthly_wom_frequency').text('months');
        }
    });
    $('#id_annual_frequency').on("spinstop", function( event, ui ) {
        if ($(this).val() == 1) {
            $('#label__annual_frequency').text('year');
        }
        else {
            $('#label__annual_frequency').text('years');
        }
    });

    // Submit post on submit
//    $('#form__payment_detail').on('submit', submit_payment_detail_form);
};

var submit_payment_detail_form = function(event){
    event.preventDefault();

    if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
        if ($("input[name='radio__monthly_style']:checked").val() == 'day_of_month') {
            $("#id_monthly_dom").val($('#select__monthly_dom_day').val());
            if ($('#select__monthly_dom_last').val() == 'last') {
                $("#id_monthly_dom").val($("#id_monthly_dom").val() * -1);
            }
            $('#id_monthly_frequency').val($('#input__monthly_dom_frequency').val());
        }
        else {
            $('#id_monthly_wom').val($('#select__monthly_wom_nth').val());
            if ($('#select__monthly_wom_last').val() == 'last') {
                $("#id_monthly_wom").val($("#id_monthly_wom").val() * -1);
            }
            $('#id_monthly_dow').val($('#select__monthly_wom_day').val());
            $('#id_monthly_frequency').val($('#input__monthly_wom_frequency').val());
        }

    } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
        $("#id_weekly_frequency").val($('#input__weekly_dow_frequency').val());
    }

    $("#id_action").val('update');
    console.info("form submitted: " + $('#form__payment_detail').serialize())  // sanity check
    processUpdatePayment();
}

var initialiseFrequencyDetails = function() {
    $('#span__weekly_dow_day').find('input:checkbox').each(function() { $(this).prop('checked',false) });
    $('#id_weekly_dow_' + moment($("#id_next_date").val(), 'DD/MM/YYYY').format('ddd').toLowerCase()).prop('checked',true);
    $("#span__weekly_dow_day").buttonset('refresh');

    if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
        $('#td__payment_schedule__monthly').show();
        $('#td__payment_schedule__weekly').hide();
        $('#td__payment_schedule__annual').hide();

        if ($('#id_next_date').val()) {
            $('input:radio[name=radio__monthly_style]').filter('[value="day_of_month"]').prop('checked', true);
            $('#select__monthly_dom_day').val($("#id_next_date").datepicker('getDate').getDate());
            $('#select__monthly_dom_day').trigger("chosen:updated");

            $('#select__monthly_wom_nth').val(Math.ceil($("#id_next_date").datepicker('getDate').getDate() / 7));
            $('#select__monthly_wom_nth').trigger("chosen:updated");
            $('#select__monthly_wom_day').val(($("#id_next_date").datepicker('getDate').getDay() + 6) % 7);
            $('#select__monthly_wom_day').trigger("chosen:updated");
        }

    } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
        $('#td__payment_schedule__monthly').hide();
        $('#td__payment_schedule__weekly').show();
        $('#td__payment_schedule__annual').hide();

    } else if ($('.select__schedule_frequency option:selected').text() == "Annual") {
        $('#td__payment_schedule__monthly').hide();
        $('#td__payment_schedule__weekly').hide();
        $('#td__payment_schedule__annual').show();

        if ($('#id_next_date').val()) {
            $('#id_annual_dom').val($("#id_next_date").datepicker('getDate').getDate());
            $('#id_annual_dom').trigger("chosen:updated");
            $('#id_annual_moy').val($("#id_next_date").datepicker('getDate').getMonth() + 1);
            $('#id_annual_moy').trigger("chosen:updated");
            $('#id_annual_frequency').val(1);
        }

    } else {
        $('#td__payment_schedule__monthly').hide();
        $('#td__payment_schedule__weekly').hide();
        $('#td__payment_schedule__annual').hide();
    }

    $('#td__payment_schedule__monthly').find('select').each(function () { $(this).trigger("chosen:updated"); });
}

var processUpdatePayment = function()  {
    var payload;
    if ($(this).text() === "Update") {     // Update button pressed
        payload = "payment_id=" + $(this).closest('button').data('payment_id') + "&action=view";
    } else if ($(this).text() === "+ Add Payment") {    //todo: don't think that this is required anymore
        payload = "action=blank";
        $(this).button( "disable" );

        var config = {
            type: "POST",
            url: URL__UPDATE_PAYMENT,
            data: payload,
            dataType: 'html',
            success: processUpdatePaymentServerResponse,
            error: ajaxErr,
            cache: false
        };
        $.ajax(config);

    } else if ($(this).text() === "Delete") {
        payload = "action=delete&payment_id=" + $(this).data('payment_id');
    } else {
        payload = $('#form__payment_detail').serialize();
    }
    console.info('processUpdatePayment:- payload: ' + payload)
    var config = {
        type: "POST",
        url: URL__UPDATE_PAYMENT,
        data: payload,
        dataType: 'html',
        success: processUpdatePaymentServerResponse,
        error: ajaxErr,
        cache: false
    };
    $.ajax(config);
}

var processUpdatePaymentServerResponse = function(serverResponse_data, textStatus_ignored, jqXHR_ignored)  {
    try {
        var o = JSON.parse(serverResponse_data);
        console.info("processUpdatePaymentServerResponse:- serverResponse_data: " + serverResponse_data);

        // look for errors
        if (o["result_success"] == "pass") {
            payments_table.ajax.reload( paymentListInitComplete );
        } else {
            $('#form__payment_detail input').each( function() {
                if (o[this.id.substring(3, this.id.length)]) {
                    console.info('Found error for ' + this.id);
                    // set the text of the error table cell to the message
                    $(this).closest("td").next().text(o[this.id.substring(3, this.id.length)][0]['message']);
                }
            });
        }
        $('#payment_detail').text(o['result_message']);
    } catch (e) {
//        JSON not received, so probably html with the initial render of the form
        $('#payment_detail').html(serverResponse_data);
    }
}

function updatePaymentList(form_data) {
    try {
        pk = form_data.payment_id;
        if ($('td[data-payment_id=' + pk + ']'))    // Update existing row
        {
            for (k in form_data) {
                var el = $('.payment_list__' + k + '[data-payment_id=' + pk + ']');
                if (el == undefined) continue;

                if (k == 'in_out') {
                    $(el).text((form_data[k] == 'i') ? 'Incoming' : 'Outgoing');
                } else {
                    $(el).text(form_data[k]);
                }

                if ($(el).hasClass('money')) {
                    $(el).autoNumeric('init', {aSign: '$'});
                }

                $(el).addClass('recently-updated');

            }
            // refresh calendar view
            loadCalendar();
        } else {    // add new row
            payments_table = $('#table__payments').DataTable();

            payments_table.row.add( {
                "Type":         form_data.payment_type_name,
                "Category":     form_data.category_name,
                "Subcategory":  form_data.subcategory_name,
                "Payment":      form_data.title,
                "In/Out":       form_data.in_out,
                "Frequency":    form_data.schedule_frequency,
                "Next Payment": form_data.next_date
            } ).draw();
        }
    } catch (e) {
        $('#payment_detail').text(e);
    }
}
