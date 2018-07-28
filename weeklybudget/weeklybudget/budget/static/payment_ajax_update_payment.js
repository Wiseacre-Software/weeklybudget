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
    // init UI elements
    $('#form__payment_detail button, #form__payment_detail input:submit').button();

    var rgx = new RegExp('[^0-9.]');
    if (rgx.test($('input.money').val())) {
        $('input.money').val($('input.money').val().replace(/[^0-9.]/g, ''));   // clean up amount if necessary
        $('input.money').autoNumeric('init', {aSign: '$'});
        $('input.money').autoNumeric('set', $('input.money').val());
    } else {
        $('input.money').autoNumeric('init', {aSign: '$'});
    }
    $('#id_in_out').chosen({width: "95%"});
    $('#id_account').chosen({width: "95%"});

    initUpdateSchedule();
    initialiseCombos();
//    initialiseFrequencyDetails();

    // hook up events
    $('#button__manage_categories').click(_.debounce(function (event) {
        event.preventDefault();
        $(this).button("disable");
        var payload = 'curr_payment_type=' + $('#id_payment_type_chosen .chosen-single').text()
            + '&curr_category=' + $('#id_category_chosen .chosen-single').text()
            + '&curr_subcategory=' + $('#id_subcategory_chosen .chosen-single').text();
        processManageCategories(payload);
    },MILLS_TO_IGNORE_CLICKS, true));
    $('#button__update_payment_save_changes').click( function(event){
        event.preventDefault();

        var validation_error = validate_schedule_fields();
        if (validation_error != '') {
            user_message('fail', validation_error);
            return false;
        }

        update_schedule_fields();
        $("#id_action").val('update');
        console.info("form submitted: " + $('#form__payment_detail').serialize())  // sanity check
        processUpdatePayment();
    } );
    $('#button__update_payment_cancel').click(function() {
        event.preventDefault();
        $('.tr__calendar_inline_edit_row').remove();
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

    // for Add Payment functionality
    if ($('#id_title').val() === '') {
        $( "#button__update_payment_save_changes" ).button( "option", "label", "Add" );
        $('#id_category').val('0');
        $('#id_category').trigger("chosen:updated");
        $('#id_subcategory').val('0');
        $('#id_subcategory').trigger("chosen:updated");
    }
};

var update_schedule_fields = function() {
   if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
        if ($("input[name='radio__monthly_style']:checked").val() == 'day_of_month') {
            $("#id_monthly_dom").val($('#select__monthly_dom_day').val());
            if ($('#select__monthly_dom_last').val() == 'last') {
                $("#id_monthly_dom").val($("#id_monthly_dom").val() * -1);
            }
            $('#id_monthly_frequency').val($('#input__monthly_dom_frequency').val());

            $('#id_monthly_wom').val(0);
            $('#id_monthly_dow').val(0);
        }
        else {
            $('#id_monthly_wom').val($('#select__monthly_wom_nth').val());
            if ($('#select__monthly_wom_last').val() == 'last') {
                $("#id_monthly_wom").val($("#id_monthly_wom").val() * -1);
            }
            $('#id_monthly_dow').val($('#select__monthly_wom_day').val());
            $('#id_monthly_frequency').val($('#input__monthly_wom_frequency').val());

            $("#id_monthly_dom").val(0);
        }

    } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
        $("#id_weekly_frequency").val($('#input__weekly_dow_frequency').val());
    }

    $("#id_until_type").val($("input[name='radio__until']:checked").val());
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
        user_message(o['result_success'], o['result_message']);
        if (o["result_success"] == "pass") {
            refresh_calendar_search_terms(o["search_terms"]);
            reloadCalendar();
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
