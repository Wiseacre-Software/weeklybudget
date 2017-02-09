var calendar_table;
var calendar_start_date = new Date(0);
var calendar_end_date = moment().add(1, 'M');
var calendar_editing_target_element;
var calendar_editing_payment_id;
var calendar_editing_payment_date;

function initCalendarView() {
    // hook up events

    // initialise UI
    $('#table__calendar .money').autoNumeric('init', {aSign: '$'});

    // datatables
    $.fn.dataTable.moment( 'L' );
    calendar_table = $('#table__calendar').DataTable({
        "ordering": false,
        "paging": false,
        "columnDefs": [ {
            "targets": 'hide-in-compact',
            "visible": true
        } ],
        "ajax": {
            method: "POST",
            url: URL__CALENDAR_VIEW,
            data: function ( d ) {
                d.start_date = moment(calendar_start_date).format('YYYY-MM-DD');
                d.end_date =  moment(calendar_end_date).format('YYYY-MM-DD');
            }
        },
        "columns": [
            {
                data: 'payment_date',
                render: function ( data, type, row ) {
                    return (moment(data).format("L"));
                },
                className: "dt-center calendar__payment_date"
            },
            {
                data: 'payment_type',
                render: function ( data, type, row ) {
                    render_html = '<div class="calendar__payment_classification">'
                    render_html += '<span class="calendar__payment_type">' + data + "</span>"
                    if (row.category) {
                        render_html += ' - <br/><span class="calendar__category">' + row.category + "</span>"
                    }
                    if (row.subcategory) {
                        render_html += ' - <br/><span class="calendar__subcategory">' + row.subcategory + "</span>"
                    }
                    render_html += '</div>'
                    return (render_html);
                },
                className: "dt-nowrap"
            },
            {
                data: 'title',
                className: "calendar__title"
            },
            {
				data: 'amount',
                render: function ( data, type, row ) {
                    return (row.in_out == 'o') ? data : '';
                },
                className: "calendar__outgoing money"
            },
            {
				data: 'amount',
                render: function ( data, type, row ) {
                    return (row.in_out == 'i') ? data : '';
                },
                className: "calendar__incoming money"
            },
            {
				data: 'curr_balance',
                className: "calendar__curr_balance money"
            },
            {
                data: 'payment_id',
                render: function ( data, type, row ) {
                    var render_html = "<button class='button-paid-received' data-payment_id='" + data + "'>Mark Payment as Paid/Received</button>"
                     render_html += "<button class='button-insert-payment' data-payment_id='" + data + "' "
                     + "data-payment_date='" + moment(row.payment_date).format("YYYY-MM-DD") + "'>Insert New Payment</button>"
                    return (render_html);
                },
                className: "calendar__actions dt-center"
            }
        ],
        "createdRow": function( row, data, dataIndex ) {
            $(row).attr('data-payment_id', data['payment_id']);
            $(row).addClass('tr-dt');
        }
    });

    $('#table__calendar').on( 'draw.dt', calendarLoadComplete);

//    $('#table__calendar thead').on( 'click', 'th', function () {
//        var $this = $(this);
//        if ($this.text() == 'Type' || $this.text() == 'Category' || $this.text() == 'Subcategory' || $this.text() == 'Name') {
//            var visibility = calendar_table.column(1).visible();
//            calendar_table.column(1).visible(!visibility);
//            calendar_table.column(2).visible(!visibility);
//            calendar_table.column(3).visible(!visibility);
//        }
//    } );

}

var calendarLoadComplete = function( settings, json ) {
//            $('div.loading').remove();

    // Make sure pop-up is not displayed
    $('#calendar__overlay').hide();
    $('#div__calendar').removeClass('ui-widget-overlay');

    $('#table__calendar td.money').autoNumeric('init', {aSign: '$'});
    $('#table__calendar .button-paid-received')
        .button( {
            icons: { primary: 'ui-icon-check', secondary: null },
            text: false
        })
        .click(_.once(processCalendarMarkAsPaidReceived));
    $('#table__calendar .button-insert-payment')
        .button( {
            icons: { primary: 'ui-icon-plus', secondary: null },
            text: false
        })
        .click(_.debounce(insertPayment, MILLS_TO_IGNORE_CLICKS, true));
    $('#table__calendar tr:last').after(
        '<tr>'
            + '<td colspan="9" style="text-align: center">'
                + '<button id="button__calendar_load_more" style="width: 95%">Load More</button>'
            + '</td>'
        + '</tr>');
    $('#button__calendar_load_more').button();
    $('#table__calendar').on('click', '#button__calendar_load_more', function(event) {
        calendar_start_date = moment(calendar_end_date).add(1, 'd');
        calendar_end_date = moment(calendar_end_date).add(1, 'M');

        $.ajax({
                type: "POST",
                url: URL__CALENDAR_VIEW,
                data: {
                    start_date: moment(calendar_start_date).format('YYYY-MM-DD'),
                    end_date: moment(calendar_end_date).format('YYYY-MM-DD')
                }
            })
            .done(function (server_response) {
                console.info('calendarLoadComplete:- server_response: ' + server_response['data']);
                calendar_table.rows.add(server_response['data']).draw();
            });
    });

    // Editing functions
    $('.calendar__payment_date').click(_.debounce(function(event) {
        $(this).off('click');
        calendar_editing_target_element = $(this);
        calendar_editing_payment_id = $(this).closest('tr').data('payment_id');
        var payload = {
            action: 'view',
            snippet: 'snippet__update_payment_date.html',
            payment_id: calendar_editing_payment_id
        }
        console.info('calendar__payment_date.click:- payment_id: ' + calendar_editing_payment_id);
        calendarUpdatePaymentDetails(payload);
    }, MILLS_TO_IGNORE_CLICKS, true));
    $('.calendar__payment_classification').click(function(event) {
        calendar_editing_target_element = $(this);
        calendar_editing_payment_id = $(this).closest('tr').data('payment_id');
        calendar_editing_payment_date = $(calendar_editing_target_element).closest('td').siblings('.calendar__payment_date').text();
        var payload = {
            action: 'view',
            snippet: 'snippet__update_payment_classification.html',
            payment_id: calendar_editing_payment_id
        }
        calendarUpdatePaymentDetails(payload);
    });
}

var insertPayment = function() {
    calendar_editing_target_element = $(this);
    calendarUpdatePaymentDetails("action=blank");
}

var calendarUpdatePaymentDetails = function (payload) {
    console.info("calendarUpdatePaymentDetails: entering, payload: " + payload);

    var jqxhr = $.ajax({
            method: "POST",
            url: URL__UPDATE_PAYMENT,
            data: payload
        })
        .done(function(serverResponse_data) {
            try {
                var o = JSON.parse(serverResponse_data);
                console.warn("calendarUpdatePaymentDetails:- serverResponse_data: " + serverResponse_data);
            } catch (e) {
                console.info('calendarUpdatePaymentDetails:- calendar_editing_target_element: ' + $(calendar_editing_target_element).prop('id'));
                // New payment or update date/frequency
                if ($(calendar_editing_target_element).hasClass('button-insert-payment')
                        || $(calendar_editing_target_element).hasClass('calendar__payment_date')) {
                    new_row = '<tr class="tr__calendar_inline_edit_row">';
                    new_row += '<td colspan="' + ($(calendar_editing_target_element).closest('td').siblings('td').length + 1) + '">';
                    new_row += serverResponse_data;
                    new_row += '</td></tr>';
                    $(calendar_editing_target_element).closest('tr').after(new_row);
                    $new_row = $(calendar_editing_target_element).closest('tr').next('tr');
                    $new_row.find("#id_next_date").val(
                        ($(calendar_editing_target_element).hasClass('calendar__payment_date'))
                            ? $(calendar_editing_target_element).text()
                            : $(calendar_editing_target_element).closest('td').siblings('.calendar__payment_date').text()
                    );
                    $new_row.find("#id_title").focus();

                // Edit date and frequency
//                } else if ($(calendar_editing_target_element).hasClass('calendar__payment_date')) {
//                    $('#calendar__overlay')
//                        .html(serverResponse_data)
//                        .show()
//                        .position({
//                            my: "left+10 top",
//                            at: "right bottom",
//                            of: calendar_editing_target_element,
//                            collision: "fit"
//                        });

                // Edit Payment Type/Category/Subcategory
                } else if ($(calendar_editing_target_element).hasClass('calendar__payment_classification')) {
                    $(calendar_editing_target_element).off('click').html(serverResponse_data);

                    $payment_type = $(calendar_editing_target_element).find('#id_payment_type');
                    $category = $(calendar_editing_target_element).find('#id_category');
                    $subcategory = $(calendar_editing_target_element).find('#id_subcategory');

                    $payment_type
                        .attr('data-placeholder', "Select a Payment Type")
                        .chosen()
                        .change(function () {
                            // select correct category
                            var c = categoryMapLookup('payment_type', $(this).val());
                            $category.val(c[1]);
                            $subcategory.val(c[2]);
                            $category.trigger("chosen:updated");
                            $subcategory.trigger("chosen:updated");
                        });
                    $category
                        .chosen({ allow_single_deselect: true })
                        .change(function () {
                            // select correct category
                            var c = categoryMapLookup('category', $(this).val());
                            $payment_type.val(c[0]);
                            $subcategory.val(c[2]);
                            $payment_type.trigger("chosen:updated");
                            $subcategory.trigger("chosen:updated");
                        });
                    $subcategory
                        .chosen({ allow_single_deselect: true } )
                        .change(function () {
                            // select correct category
                                var c = categoryMapLookup('subcategory', $(this).val());
                                $payment_type.val(c[0]);
                                $category.val(c[1]);
                                $payment_type.trigger("chosen:updated");
                                $category.trigger("chosen:updated");
                            });

                    $(calendar_editing_target_element).find('.button__calendar_edit__classification_update')
                        .button( {
                            icons: { primary: 'ui-icon-disk', secondary: null },
                            text: false
                        })
                        .click(_.once(function (event) {
                            var payload = $('#form__payment_detail').serialize();
                            calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_CLASSIFICATION, payload);
                        }));
                    $(calendar_editing_target_element).find('.button__calendar_edit__classification_edit')
                        .button( {
                            icons: { primary: 'ui-icon-pencil', secondary: null },
                            text: false
                        });
                        //TODO .click(_.once(updatePaymentClassification));
                }
            }
        })
        .fail(ajaxErr);
}

var initCalendarUpdatePayment = function() {
    // init UI elements
    $('#form__payment_detail button, #form__payment_detail input:submit').button();
    $("#id_next_date").datepicker({dateFormat: "dd/mm/yy", showButtonPanel: true});
    $('#input__weekly_dow_frequency').spinner({min: 1});
    $("#span__weekly_dow_day").buttonset();
    $('#input__monthly_dom_frequency').spinner({min: 1});
    $('#input__monthly_wom_frequency').spinner({min: 1});
    $('#id_annual_frequency').attr('type', 'text').spinner({min: 1});
    $('#form__payment_detail input[name="rdo__series_choice"]').checkboxradio();
    $('#form__payment_detail input[name="radio__monthly_style"]').checkboxradio();

    if ($("#id_next_date").val() === '') {
        $("#id_next_date")
            .val(moment(new Date()).format('DD/MM/YYYY'))
            .change();
    }
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

    // init UI state
    $('#form__payment_detail input[name="radio__monthly_style"]')
        .click(function(event) {
            $( '#form__payment_detail input[name="radio__monthly_style"]' ).checkboxradio( "refresh" );
        });
    initialiseCombos();
    $('.select__schedule_frequency').change(initialiseCalendarFrequencyDetails);
    if ($('#id_is_exclusion').val() == 'False') {
        $('#button__update_payment_date_revert_to_schedule').hide();
    } else {
        $('.td__series_choice').hide();
    }
    if ($('#id_title').val() === '') {
        $('#button__update_payment_date_save_changes').val('Add');
    }

    // UI events
    $('#form__payment_detail input[name="rdo__series_choice"]').change(function() {
        if($(this).val() == 'this') {
            $('.tr__payment_details_frequency').hide();
            $('#tr__payment_schedule__monthly').hide();
            $('#tr__payment_schedule__weekly').hide();
            $('#tr__payment_schedule__annual').hide();
            $('#form__payment_detail input[name="rdo__series_choice"]').val('this');
        } else {
            $('.tr__payment_details_frequency').show();
            $('#form__payment_detail input[name="rdo__series_choice"]').val('series');
            initialiseCalendarFrequencyDetails();
        }
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

    $("#input__weekly_dow_frequency").spinner('value', 1).on("spinstop", function( event, ui ) {
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

    $('#button__update_payment_date_save_changes').click(function(event) {
        event.preventDefault();

        $('#div__update_payment_date_result').empty();
        if ($('#form__payment_detail input[name="rdo__series_choice"]').val() == 'this') {
            var payload = jQuery.param({
                series_choice: 'this',
                payment_id: $('#form__payment_detail #id_payment_id').val(),
                next_date: $('#form__payment_detail #id_next_date').val(),
                original_date: moment($(calendar_editing_target_element).text(), 'L').format('YYYY-MM-DD')
            });
        } else {
            $("#id_weekly_frequency").val($("#input__weekly_dow_frequency").spinner('value'));
            payload = $('#form__payment_detail').serialize()
                .replace('rdo__','');
        }
        debugger;
        calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_DATE, payload);
    });

    $('#button__update_payment_date_cancel').click(function(event) {
        event.preventDefault();
        $('#calendar__overlay').hide();
        $('#div__calendar').removeClass('ui-widget-overlay');
    })

    $('#button__update_payment_date_revert_to_schedule')
        .click(function(event) {
            event.preventDefault();

            $('#div__update_payment_date_result').empty();

            var payload = jQuery.param({
                action: 'revert',
                payment_id: $('#form__payment_detail #id_payment_id').val(),
                });
            calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_DATE, payload);
        })
        .tooltip({
            items: 'button',
            content: "Revert this payment back to its original schedule"
        });
}

var initialiseCombos = function() {
    // build combos
    var day = [];
    for (var i = 1; i <= 31; i++) {
        day.push(i);
    }
    $.each(day, function (index, d) {
        var dayth;
        switch (d % 10) {
            case 1:
                dayth = (d == 11) ? d + 'th' : d + 'st';
                break;
            case 2:
                dayth = (d == 12) ? d + 'th' : d + 'nd';
                break;
            case 3:
                dayth = (d == 13) ? d + 'th' : d + 'rd';
                break;
            default:
                dayth = d + 'th';
        }
        if (d <= 5) {
            $("#select__monthly_wom_nth").append("<option value='" + d + "'>" + dayth + "</option>");
        }
        if (d <= 31) {
            $("#select__monthly_dom_day").append("<option value='" + d + "'>" + dayth + "</option>");
        }
    });

    // initial values
    if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
        if ($("#id_monthly_dom").val() != 0) {
            $('input[name=radio__monthly_style]').val(['day_of_month']);
            $("#select__monthly_dom_day").val(Math.abs($("#id_monthly_dom").val()));
            if ($("#id_monthly_dom").val() < 0) $('#select__monthly_dom_last').val('last');
            $("#input__monthly_dom_frequency").val($("#id_monthly_frequency").val());

            $('#select__monthly_wom_nth').val(Math.ceil(Math.abs($("#id_monthly_dom").val()) / 7));
            if ($("#id_monthly_dom").val() < 0) $('#select__monthly_wom_last').val('last');
            $('#select__monthly_wom_day').val(($('#id_next_date').datepicker('getDate').getDay() + 6) % 7);
            $("#input__monthly_wom_frequency").val($("#id_monthly_frequency").val());

            if ($("#id_monthly_frequency").val() == 1) {
                $('#label__monthly_dom_frequency').text('month');
                $('#label__monthly_wom_frequency').text('month');
            }
            else {
                $('#label__monthly_dom_frequency').text('months');
                $('#label__monthly_wom_frequency').text('months');
            }
        } else {
            $('input[name=radio__monthly_style]').val(['day_of_week']);
            $("#select__monthly_wom_nth").val(Math.abs($("#id_monthly_wom").val()));
            if ($("#id_monthly_wom").val() < 0) $('#select__monthly_wom_last').val('last');
            $("#select__monthly_wom_day").val($("#monthly_dow").val());
            $("#input__monthly_wom_frequency").val($("#id_monthly_frequency").val());
            if ($("#id_monthly_frequency").val() == 1) {
                $('#label__monthly_wom_frequency').text('month');
            }
            else {
                $('#label__monthly_wom_frequency').text('months');
            }
        }
        $( '#form__payment_detail input[name="radio__monthly_style"]' ).checkboxradio( "refresh" );

    } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
        $("#input__weekly_dow_frequency").spinner('value', $("#id_weekly_frequency").val());
//        $("#input__weekly_dow_frequency").val($("#id_weekly_frequency").val());
        if ($("#id_weekly_frequency").val() == 1) {
            $('#label__weekly_dow_frequency').text('week');
        }
        else {
            $('#label__weekly_dow_frequency').text('weeks');
        }
    }

    $('#td__payment_schedule__monthly').find('select').each(function () { $(this).trigger("chosen:updated"); });
}

var initialiseCalendarFrequencyDetails = function() {
    $('#span__weekly_dow_day').find('input:checkbox').each(function() { $(this).prop('checked',false) });
    $('#id_weekly_dow_' + moment($("#id_next_date").val(), 'DD/MM/YYYY').format('ddd').toLowerCase()).prop('checked',true);
    $("#span__weekly_dow_day").buttonset('refresh');

    if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
        $('#tr__payment_schedule__monthly').show();
        $('#tr__payment_schedule__weekly').hide();
        $('#tr__payment_schedule__annual').hide();

    } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
        $('#tr__payment_schedule__monthly').hide();
        $('#tr__payment_schedule__weekly').show();
        $('#tr__payment_schedule__annual').hide();

    } else if ($('.select__schedule_frequency option:selected').text() == "Annual") {
        $('#tr__payment_schedule__monthly').hide();
        $('#tr__payment_schedule__weekly').hide();
        $('#tr__payment_schedule__annual').show();

    } else {
        $('#tr__payment_schedule__monthly').hide();
        $('#tr__payment_schedule__weekly').hide();
        $('#tr__payment_schedule__annual').hide();
    }

    $('#tr__payment_schedule__monthly').find('select').each(function () { $(this).trigger("chosen:updated"); });
}

var calendarUpdatePaymentInline = function (ajax_url, payload) {
    var jqxhr = $.ajax({
            method: "POST",
            url: ajax_url,
            data: payload
        })
        .done(function(serverResponse_data) {
            console.info("updatePaymentClassification:- serverResponse_data: " + serverResponse_data);
            try {
                if (serverResponse_data['result_success'] == 'pass') {
                    $('#div__update_payment_result').children('.result-message-text').text('Update successful!');
                    $('#div__update_payment_result').children('.ui-icon').addClass('ui-icon-circle-check');
                    $('#div__update_payment_result')
                        .addClass('result-message-box-success')
                        .show();

                    reloadCalendar();
                } else {
                    $('#div__update_payment_result')
                        .children('.result-message-text')
                        .html('<strong>Update failed!</strong> ' + serverResponse_data['result_message']);
                    $('#div__update_payment_result').children('.ui-icon').addClass('ui-icon-alert');
                    $('#div__update_payment_result')
                        .show();
                }
//                console.info("calendarUpdatePaymentDetails:- serverResponse_data: " + serverResponse_data);
            } catch (e) {

            }
        })
        .fail(ajaxErr);
}

var processCalendarMarkAsPaidReceived = function () {
    $(this).off('click');
    received_date = moment($(this).closest('td').siblings('.calendar__payment_date').text(), 'L').format('YYYY-MM-DD');
	var payload = "action=update&payment_id=" + $(this).data('payment_id')
					+ "&payment_date=" + received_date
					+ '&start_date=' + moment(calendar_start_date).format('YYYY-MM-DD')
                    + '&end_date=' + moment(calendar_end_date).format('YYYY-MM-DD');

    var config = {
        type: "POST",
        url: URL__CALENDAR_VIEW,
        data: payload,
        success: reloadCalendar,
        error: ajaxErr,
        cache: false
    };
    $.ajax(config);
}

var reloadCalendar = function() {
	calendar_table.ajax.reload( );
//	calendar_table.ajax.reload( calendarLoadComplete );
}

var processLoadCalendarServerResponse = function(serverResponse_data, textStatus_ignored, jqXHR_ignored) {
    try {
        var o = JSON.parse(serverResponse_data);
//        console.info("processLoadCalendarServerResponse:- serverResponse_data: " + serverResponse_data);
//        $('.calendar_view').text(o['result']);
    } catch (e) {
//        console.info("processLoadCalendarServerResponse:- serverResponse_data: " + serverResponse_data);
        $('.calendar_view').html(serverResponse_data);
    }
}

