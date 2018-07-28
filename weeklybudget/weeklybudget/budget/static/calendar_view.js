var calendar_table;
var calendar_start_date = new Date(0);
var calendar_end_date = moment().add(1, 'M');
var calendar_editing_original_html;
var calendar_editing_payment_id;
var calendar_editing_payment_date;
var calendar_editing_row_id;
var calendar_editing_target_element;
var calendar_selected_row_id;
var calendar_final_balance;

(function($) {
    $.fn.scrollToPayment = function() {
        $('#div__calendar').animate({
            scrollTop: ($('#div__calendar').scrollTop() + $(this).offset().top - $('#div__calendar').offset().top) + 'px'
        }, 'fast');
        return this; // for chaining...
    }
})(jQuery);

(function($) {
    $.fn.scrollToInlineForm = function() {
        $('#div__calendar').animate({
            scrollTop: ($('#div__calendar').scrollTop()
                    + $(this).offset().top
                    + $(this).height()
                    - $('#div__calendar').offset().top
                    - $('#div__calendar').height()) + 'px'
        }, 'fast');
        return this; // for chaining...
    }
})(jQuery);

function initCalendarView() {
    // hook up events

    // initialise UI
    $('#table__calendar tbody .money').autoNumeric('init', {aSign: '$'});
    $('#txt__calendar_search')
        .autocomplete({ source: calendar_search_terms })
        .keydown(function(event){
            if(event.keyCode == 13) {
              if($(this).val().length !== 0) {
//                  event.preventDefault();
                  $('#btn__calendar_search_next').focus().click();
                  return false;
              }
            }
         });
    $('#btn__calendar_search_next').button( {
            icons: { primary: 'ui-icon-triangle-1-s', secondary: null },
            text: false
        })
        .click(_.debounce(function(){ return calendar_search( false, 'forwards' ); }, MILLS_TO_IGNORE_CLICKS, true));
    $('#btn__calendar_search_prev').button( {
            icons: { primary: 'ui-icon-triangle-1-n', secondary: null },
            text: false
        })
        .click(_.debounce(function(){ return calendar_search( false, 'backwards' ); }, MILLS_TO_IGNORE_CLICKS, true));
    $('#btn__calendar_new_payment_from_search').button( {
            icons: { primary: 'ui-icon-plus', secondary: null },
            text: false
        })
       .click(_.debounce(function () {
            calendar_editing_target_element = $('#table__calendar').find('.button-insert-payment:first');
            calendarUpdatePaymentDetails("action=blank&title=" + $('#txt__calendar_search').val());
        }, MILLS_TO_IGNORE_CLICKS, true));

    // datatables
    $.fn.dataTable.moment( 'L' );
    calendar_table = $('#table__calendar').DataTable({
        "ordering": false,
        "paging": false,
        "searching": false,
        fixedHeader: true,
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
                className: "dt-center calendar__payment_date calendar__searchable"
            },
            {
                data: 'payment_type',
                render: render_category,
                className: "dt-nowrap calendar__searchable"
            },
            {
                data: 'title',
                className: "calendar__title calendar__searchable"
            },
            {
                data: 'account',
                className: "calendar__account calendar__searchable"
            },
            {
				data: 'amount',
                render: function ( data, type, row ) {
                    return (row.in_out == 'o') ? data : '';
                },
                className: "calendar__outgoing money calendar__searchable"
            },
            {
				data: 'amount',
                render: function ( data, type, row ) {
                    return (row.in_out == 'i') ? data : '';
                },
                className: "calendar__incoming money calendar__searchable"
            },
            {
				data: 'curr_balance',
				render: function ( data, type, row ) {
//				    var render_html = '<div class=" calendar__searchable">'
                    var render_html = '<div class="calendar__curr_budget_balance money">' + data + "</div>"
                    render_html += '<div class="calendar__curr_balance money">' + row.curr_budget_balance + "</div>"
//                    render_html += '</div>'
                    return (render_html);
                },
                className: "calendar__balance dt-center"
            },
            {
                data: 'payment_id',
                render: function ( data, type, row ) {
                    var render_html = "<button class='button-paid-received' data-payment_id='" + data + "'>Mark Payment as Paid/Received</button>";
                    render_html += "<button class='button-insert-payment' data-payment_id='" + data + "' "
                     + "data-payment_date='" + moment(row.payment_date).format("YYYY-MM-DD") + "'>Insert New Payment</button>";
                    render_html += "<button class='button__delete_payment' data-row_id='" + data + "|" + row.payment_date + "'>Delete Payment</button>";
                    return (render_html);
                },
                className: "calendar__actions dt-center dt-nowrap"
            }
        ],
        "createdRow": function( row, data, dataIndex ) {
            $(row).attr('data-payment_id', data['payment_id']);
            $(row).attr('data-row_id', data['row_id']);
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
    calendar_end_date = new Date(json.json['calendar_end_date']);    // only works on initial load
    calendar_final_balance = json.json["final_balance"];    // only works on initial load
//    console.info('calendarLoadComplete:- and were back, final_balance: ' + calendar_final_balance);
//            $('div.loading').remove();

    // Make sure pop-up is not displayed
    $('#calendar__overlay').hide();
    $('#div__calendar').removeClass('ui-widget-overlay');

    // Re-select any selected rows
    if (calendar_selected_row_id) {
        $('#table__calendar').find('tr[data-row_id="' + calendar_selected_row_id + '"] td').each( function () {
            $(this).addClass( 'highlight' );
        });
    }

    $('#table__calendar tbody .money').autoNumeric('init', {aSign: '$'});
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
        .click(_.debounce(function () {
            calendar_editing_target_element = $(this);
            calendarUpdatePaymentDetails("action=blank");
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#table__calendar .button__delete_payment')
        .button( {
            icons: { primary: 'ui-icon-trash', secondary: null },
            text: false
        })
        .click(_.debounce(deletePayment, MILLS_TO_IGNORE_CLICKS, true));
    $('#table__calendar tr:last').after(
        '<tr>'
            + '<td colspan="9" style="text-align: center">'
                + '<button id="button__calendar_load_more" style="width: 95%">Load More</button>'
            + '</td>'
        + '</tr>');
    $('#button__calendar_load_more').button();
    $('#table__calendar').on('click', '#button__calendar_load_more', function(event) {
        new_start_date = moment(calendar_end_date).add(1, 'd');
        calendar_end_date = moment(calendar_end_date).add(1, 'M');

        $.ajax({
                type: "POST",
                url: URL__CALENDAR_VIEW,
                data: {
                    start_date: new_start_date.format('YYYY-MM-DD'),
                    end_date: calendar_end_date.format('YYYY-MM-DD'),
                    final_balance: calendar_final_balance
                }
            })
            .done(function (server_response) {
                calendar_table.rows.add(server_response['data']).draw();
                calendar_end_date = new Date(server_response['calendar_end_date']);
                calendar_final_balance = server_response['final_balance']
            });
    });

    // Editing functions
    $('td.calendar__payment_date').click(_.debounce(function(event) {
        reset_editing_state();
        if ( $('.tr__calendar_inline_edit_row').length ) {
            $('.tr__calendar_inline_edit_row').remove();
        } else {
            calendar_editing_target_element = $(this);
            calendar_editing_payment_id = $(this).closest('tr').data('payment_id');
            var payload = {
                action: 'view',
                snippet: 'snippet__update_payment_date.html',
                payment_id: calendar_editing_payment_id
            }
            calendarUpdatePaymentDetails(payload);
        }
    }, MILLS_TO_IGNORE_CLICKS, true));
    $('.calendar__payment_classification').parent('td').click(_.debounce(editPaymentCategory, MILLS_TO_IGNORE_CLICKS, true));
    $('td.calendar__title').click(_.debounce(function() { editPaymentDetail(event, 'title'); }, MILLS_TO_IGNORE_CLICKS, true));
    $('td.calendar__outgoing').click(_.debounce(function() { editPaymentDetail(event, 'outgoing'); }, MILLS_TO_IGNORE_CLICKS, true));
    $('td.calendar__incoming').click(_.debounce(function() { editPaymentDetail(event, 'incoming'); }, MILLS_TO_IGNORE_CLICKS, true));
    $('td.calendar__account').click(_.debounce(editCalendarAccount, MILLS_TO_IGNORE_CLICKS, true));
}

var render_category = function ( data, type, row ) {
    render_html = '<div class="calendar__payment_classification">'
    render_html += '<span class="calendar__payment_type" data-payment_type_id="' + row.payment_type_id + '">' + data + "</span>"
    if (row.category) {
        render_html += ' - <br/><span class="calendar__category" data-category_id="' + row.category_id + '">' + row.category + "</span>"
    }
    if (row.subcategory) {
        render_html += ' - <br/><span class="calendar__subcategory" data-subcategory_id="' + row.subcategory_id + '">' + row.subcategory + "</span>"
    }
    render_html += '</div>'
    return (render_html);
}

var editPaymentDetail = function(event, field_name) {
    reset_editing_state();

    var $this = $(event.target);
    var payment_id = $this.closest('tr').data('payment_id');
    var is_money = $this.hasClass('money')
    var this_val = (is_money) ? $this.autoNumeric('get') : $this.text();
    calendar_editing_original_html = $this.html();

    var $input_element = (is_money)
        ? $('<input />',{'value' : this_val, 'class' : 'money'}).val(this_val).autoNumeric('init', {aSign: '$'})
        : $('<input />',{'value' : this_val}).val(this_val)

    $this
        .html('')
        .addClass('nowrap')
        .append( $input_element )
        .append( $('<button />', {'text' : 'Update Series', 'class' : 'button-update-detail-save-series', 'data-payment_id' : payment_id})
            .button( {
                icons: { primary: 'ui-icon-link', secondary: null },
                text: false
            })
            .click(_.once(function (event) {
                $(this).siblings('button').button( "disable" );
                var payload = "payment_id=" + payment_id + "&field=" + field_name + "&single_series=series&value="
                    + ((is_money) ? $(this).siblings('input').autoNumeric('get') : $(this).siblings('input').val());
                calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_PARTIAL, payload);
                return false;   // prevent further propagation of button click
            })))
        .append( $('<button />', {'text' : 'Update This', 'class' : 'button-update-detail-save-single', 'data-payment_id' : payment_id})
            .button( {
                icons: { primary: 'ui-icon-check', secondary: null },
                text: false
            })
            .click(_.once(function (event) {
                $(this).siblings('button').button( "disable" );
                var payload = "payment_id=" + payment_id + "&field=" + field_name + "&single_series=single&value="
                    + ((is_money) ? $(this).siblings('input').autoNumeric('get') : $(this).siblings('input').val())
                    + '&payment_date=' + moment($(this).closest('td').siblings('.calendar__payment_date').text(), 'L').format('YYYY-MM-DD');
                calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_PARTIAL, payload);
                return false;
            })))
        .append( $('<button />', {'text' : 'Cancel', 'class' : 'button-update-detail-cancel payment_edit_cancel', 'data-payment_id' : payment_id})
            .button( {
                icons: { primary: 'ui-icon-close', secondary: null },
                text: false
            })
            .click(_.once(function (event) {
                $(this).siblings('button').button( "disable" );
                $(this).closest('td').empty().html(calendar_editing_original_html);
                return false;
            })));
    $this.find('input:first').select();
}

var editPaymentCategory = function(event) {
    reset_editing_state();
    calendar_editing_target_element = $(this).children('div');
    calendar_editing_payment_id = $(this).closest('tr').data('payment_id');
    calendar_editing_payment_date = $(this).siblings('.calendar__payment_date').text();
    var payload = {
        action: 'view',
        snippet: 'snippet__update_payment_classification.html',
        payment_id: calendar_editing_payment_id
    }
    calendarUpdatePaymentDetails(payload);
}

var editCalendarAccount = function(event) {
    reset_editing_state();
    $(this).unbind('click');
    calendar_editing_row_id = $(this).closest('tr').data('row_id');
    calendar_editing_original_html = $(this).html();
    calendar_editing_current_val = $(this).text();
    $.getJSON(URL__GET_ACCOUNTS_JSON, function(result) {
        account_list = result;
        var $tr = $('tr[data-row_id="' + calendar_editing_row_id + '"]');
        var payment_id = $tr.data('payment_id');
        var s = $('<select />', { 'class': 'cbo__edit_calendar_account' });
        for (var i = 0; i < account_list.length; i++) {
            if (account_list[i]['title'] === calendar_editing_current_val) {
                $('<option />', {value: account_list[i]['id'], text: account_list[i]['title'], selected: 'selected'}).appendTo(s);
            } else {
                $('<option />', {value: account_list[i]['id'], text: account_list[i]['title']}).appendTo(s);
            }
        }
//        var s_wrapper = $('<div />').append($('<form />').append($('<div />').append(s)));
        $tr.children('td.calendar__account')
            .empty()
            .addClass('nowrap')
            .append(s)
            .append( $('<button />', {'text' : 'Update Series', 'class' : 'button-update-account-save-series', 'data-payment_id' : payment_id})
                .button( {
                    icons: { primary: 'ui-icon-link', secondary: null },
                    text: false
                })
                .click(_.once(function (event) {
                    $(this).siblings('button').button( "disable" );
                    var payload = "payment_id=" + payment_id + "&field=account_id&single_series=series&value=" + $('.cbo__edit_calendar_account').val();
                    calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_PARTIAL, payload);
                    return false;   // prevent further propagation of button click
                })))
            .append( $('<button />', {'text' : 'Update This', 'class' : 'button-update-account-save-single', 'data-payment_id' : payment_id})
                .button( {
                    icons: { primary: 'ui-icon-check', secondary: null },
                    text: false
                })
                .click(_.once(function (event) {
                    $(this).siblings('button').button( "disable" );
                    var payload = "payment_id=" + payment_id + "&field=account_id&single_series=single&value=" + $('.cbo__edit_calendar_account').val();
                    payload += '&payment_date=' + moment($(this).closest('td').siblings('.calendar__payment_date').text(), 'L').format('YYYY-MM-DD');
                    calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_PARTIAL, payload);
                    return false;
                })))
            .append( $('<button />', {'text' : 'Cancel', 'class' : 'button-update-account-cancel payment_edit_cancel', 'data-payment_id' : payment_id})
                .button( {
                    icons: { primary: 'ui-icon-close', secondary: null },
                    text: false
                })
                .click(_.once(function (event) {
                    $(this).siblings('button').button( "disable" );
                    $(this).closest('td')
                        .empty()
                        .html(calendar_editing_original_html)
                        .click(_.debounce(editCalendarAccount, MILLS_TO_IGNORE_CLICKS, true));;
                    return false;
                })));
        $('.cbo__edit_calendar_account').chosen();
        return false;
    });
    return false;
}

var calendarUpdatePaymentDetails = function (payload) {
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
//                console.info('calendarUpdatePaymentDetails:- calendar_editing_target_element: ' + $(calendar_editing_target_element).prop('id'));
                // New payment or update date/frequency
                if ($(calendar_editing_target_element).hasClass('button-insert-payment')
                        || $(calendar_editing_target_element).hasClass('calendar__payment_date')) {
                    if ( $('.tr__calendar_inline_edit_row').length ) {
                        $('.tr__calendar_inline_edit_row').remove();
                    }
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
                    var  orig_html =  $(calendar_editing_target_element).parent().html();

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
                            icons: { primary: 'ui-icon-check', secondary: null },
                            text: false
                        })
                        .click(_.once(function (event) {
                            var payload = $('#form__payment_detail').serialize();
                            calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_CLASSIFICATION, payload);
                        }));
                    $(calendar_editing_target_element).find('.button__calendar_edit__classification_cancel')
                        .button( {
                            icons: { primary: 'ui-icon-close', secondary: null },
                            text: false
                        })
                        .click(_.debounce(function (event) {
                            $(this).closest('.calendar__payment_classification:first-child').replaceWith(orig_html);
                            return false;
                        }, MILLS_TO_IGNORE_CLICKS, true));
                    $(calendar_editing_target_element).find('.button__calendar_edit__classification_edit')
                        .button( {
                            icons: { primary: 'ui-icon-pencil', secondary: null },
                            text: false
                        })
                        .click(_.debounce(function() {
                            $(this).closest('tr').after($('<tr />', { class: 'tr__calendar_inline_edit_row' }));
                            var payload = 'curr_payment_type=' + $('#id_payment_type_chosen .chosen-single').text()
                                + '&curr_category=' + $('#id_category_chosen .chosen-single').text()
                                + '&curr_subcategory=' + $('#id_subcategory_chosen .chosen-single').text();
                            $(this).closest('.calendar__payment_classification:first-child').replaceWith(orig_html);
                            processManageCategories(payload);
                            return false;
                        }, MILLS_TO_IGNORE_CLICKS, true));
                }
            }
        })
        .fail(ajaxErr);
}

var initUpdateSchedule = function() {
    // init UI elements
    $("#id_next_date").datepicker({dateFormat: "dd/mm/yy", showButtonPanel: true});
    $('#input__weekly_dow_frequency').spinner({min: 1});
    $("#span__weekly_dow_day").buttonset();
    $('#input__monthly_dom_frequency').spinner({min: 1});
    $('#input__monthly_wom_frequency').spinner({min: 1});
    $('#id_annual_frequency').attr('type', 'text').spinner({min: 1});
    $('#id_occurrences').spinner({min: 1});
    $("#id_end_date").datepicker({dateFormat: "dd/mm/yy", showButtonPanel: true});
    $('#form__payment_detail input[name="rdo__series_choice"]').checkboxradio();
    $('#form__payment_detail input[name="radio__monthly_style"]').checkboxradio();
    $('#form__payment_detail input[name="radio__until"]').checkboxradio();

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
    $('#id_linked_to').attr('data-placeholder', "Select a Payment").chosen({width: "95%"});
    $("#id_offset").spinner()
    $('#id_offset_type').chosen({width: "100px"});

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

    // Scroll into view
    $('.tr__calendar_inline_edit_row').scrollToInlineForm();

    // UI events
    $('#form__payment_detail input[name="rdo__series_choice"]').change(function() {
        if($(this).val() == 'this') {
            $('.tr__payment_details_frequency').hide();
            $('#tr__payment_schedule__monthly').hide();
            $('#tr__payment_schedule__weekly').hide();
            $('#tr__payment_schedule__annual').hide();
            $('#tr__payment_schedule__linked').hide();
            $('#tr__payment_schedule__until').hide();
            $('#form__payment_detail input[name="rdo__series_choice"]').val('this');
        } else {
            $('.tr__payment_details_frequency').show();
            $('#form__payment_detail input[name="rdo__series_choice"]').val('series');
            initialiseCalendarFrequencyDetails();
        }

        initUpdatePaymentDate();
    });
    $('#id_next_date').change(updateCalendarSettingsForDate);

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
}

var initUpdatePaymentDate = function() {
    $('#form__payment_detail button, #form__payment_detail input:submit').button();
        $('#button__update_payment_date_save_changes').click(function(event) {
        event.preventDefault();

        var validation_error = validate_schedule_fields();
        if (validation_error != '') {
            user_message('fail', validation_error);
            return false;
        }

        $('#div__update_payment_date_result').empty();
        if ($('#form__payment_detail input[name="rdo__series_choice"]').val() == 'this') {
            var payload = jQuery.param({
                series_choice: 'this',
                payment_id: $('#form__payment_detail #id_payment_id').val(),
                next_date: $('#form__payment_detail #id_next_date').val(),
                original_date: moment($(calendar_editing_target_element).text(), 'L').format('YYYY-MM-DD')
            });
        } else {
            update_schedule_fields();
            payload = $('#form__payment_detail').serialize()
                .replace('rdo__','');
        }
        calendarUpdatePaymentInline(URL__UPDATE_PAYMENT_DATE, payload);
    });

    $('#button__update_payment_date_cancel').click(function(event) {
        event.preventDefault();
        $('#calendar__overlay').hide();
        $('#div__calendar').removeClass('ui-widget-overlay');
        $('.tr__calendar_inline_edit_row').remove();
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
}

var initialiseCalendarFrequencyDetails = function() {
    $('#span__weekly_dow_day').find('input:checkbox').each(function() { $(this).prop('checked',false) });
    $('#id_weekly_dow_' + moment($("#id_next_date").val(), 'DD/MM/YYYY').format('ddd').toLowerCase()).prop('checked',true);
    $("#span__weekly_dow_day").buttonset('refresh');

    if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
        $('#tr__payment_schedule__monthly').show();
        $('#tr__payment_schedule__weekly').hide();
        $('#tr__payment_schedule__annual').hide();
        $('#tr__payment_schedule__linked').hide();
        $('#tr__payment_schedule__until').show();
    } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
        $('#tr__payment_schedule__monthly').hide();
        $('#tr__payment_schedule__weekly').show();
        $('#tr__payment_schedule__annual').hide();
        $('#tr__payment_schedule__linked').hide();
        $('#tr__payment_schedule__until').show();
    } else if ($('.select__schedule_frequency option:selected').text() == "Annual") {
        $('#tr__payment_schedule__monthly').hide();
        $('#tr__payment_schedule__weekly').hide();
        $('#tr__payment_schedule__annual').show();
        $('#tr__payment_schedule__linked').hide();
        $('#tr__payment_schedule__until').show();
    } else if ($('.select__schedule_frequency option:selected').text() == "Linked to Other Payment") {
        $('#tr__payment_schedule__monthly').hide();
        $('#tr__payment_schedule__weekly').hide();
        $('#tr__payment_schedule__annual').hide();
        $('#tr__payment_schedule__linked').show();
        $('#tr__payment_schedule__until').show();
    } else {
        $('#tr__payment_schedule__monthly').hide();
        $('#tr__payment_schedule__weekly').hide();
        $('#tr__payment_schedule__annual').hide();
        $('#tr__payment_schedule__linked').hide();
        $('#tr__payment_schedule__until').hide();
    }

    $('#tr__payment_schedule__monthly').find('select').each(function () { $(this).trigger("chosen:updated"); });

    // initial values
    if ($('.select__schedule_frequency option:selected').text() == "Monthly") {
        if ($("#id_monthly_dom").val() == '') {  // New payment
            $('input[name=radio__monthly_style]').val(['day_of_month']);
            $("#select__monthly_dom_day").val($('#id_next_date').datepicker('getDate').getDate());
            $('#select__monthly_wom_nth').val(Math.ceil($('#id_next_date').datepicker('getDate').getDate() / 7));
            $('#select__monthly_wom_day').val(($('#id_next_date').datepicker('getDate').getDay() + 6) % 7);
        } else if ($("#id_monthly_dom").val() != 0) {
            $('input[name=radio__monthly_style]').val(['day_of_month']);
            var id_next_date_getDate = $('#id_next_date').datepicker('getDate');
            var new_day = id_next_date_getDate.getDate();
            var last_day = moment({ year: id_next_date_getDate.getFullYear(), month: id_next_date_getDate.getMonth(), day: 1 })
                .add(1, 'months').add($("#id_monthly_dom").val(), 'days').date();
            if (($("#id_monthly_dom").val() > 0 && new_day == $("#id_monthly_dom").val())
                || ($("#id_monthly_dom").val() < 0 && last_day == new_day)) {
                $("#select__monthly_dom_day").val(Math.abs($("#id_monthly_dom").val()));
                if ($("#id_monthly_dom").val() < 0) $('#select__monthly_dom_last').val('last');
                $('#select__monthly_wom_nth').val(Math.ceil(Math.abs($("#id_monthly_dom").val()) / 7));
                if ($("#id_monthly_dom").val() < 0) $('#select__monthly_wom_last').val('last');
                $('#select__monthly_wom_day').val(Math.abs($("#id_monthly_dow").val()));
            } else {
                $("#select__monthly_dom_day").val(new_day);
                $('#select__monthly_wom_nth').val(Math.ceil(new_day / 7));
                $('#select__monthly_wom_day').val((id_next_date_getDate.getDay() + 6) % 7);
            }
            $("#input__monthly_dom_frequency").val($("#id_monthly_frequency").val());
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
            $("#select__monthly_wom_day").val($("#id_monthly_dow").val());
            $("#input__monthly_wom_frequency").val($("#id_monthly_frequency").val());
            if ($("#id_monthly_frequency").val() == 1) {
                $('#label__monthly_wom_frequency').text('month');
            }
            else {
                $('#label__monthly_wom_frequency').text('months');
            }
        }
        $( '#form__payment_detail input[name="radio__monthly_style"]' ).checkboxradio( "refresh" );
        $('#tr__payment_schedule__monthly').find('select').each(function () { $(this).trigger("chosen:updated"); });

    } else if ($('.select__schedule_frequency option:selected').text() == "Weekly") {
        $("#input__weekly_dow_frequency").spinner('value', $("#id_weekly_frequency").val());
        if ($("#id_weekly_frequency").val() == 1) {
            $('#label__weekly_dow_frequency').text('week');
        }
        else {
            $('#label__weekly_dow_frequency').text('weeks');
        }
        $('#tr__payment_schedule__weekly').find('select').each(function () { $(this).trigger("chosen:updated"); });

    } else if ($('.select__schedule_frequency option:selected').text() == "Annual") {
        var next_date = $('#id_next_date').datepicker('getDate');
        $("#id_annual_dom").val(next_date.getDate());
        $("#id_annual_moy").val(next_date.getMonth() + 1);
        if ($('#id_annual_frequency').val() == 0) $('#id_annual_frequency').val('1');
        $('#tr__payment_schedule__annual').find('select').each(function () { $(this).trigger("chosen:updated"); });
    }

    $('.tr__calendar_inline_edit_row').scrollToInlineForm();
}

var calendarUpdatePaymentInline = function (ajax_url, payload) {
    var jqxhr = $.ajax({
            method: "POST",
            url: ajax_url,
            data: payload
        })
        .done(function(serverResponse_data) {
            try {
                if (serverResponse_data['result_success'] === 'pass') reloadCalendar();
                user_message(serverResponse_data['result_success'], serverResponse_data['result_message']);
                refresh_calendar_search_terms(serverResponse_data['search_terms']);
            } catch (e) {
                console.error("calendarUpdatePaymentInline:- done exception: " + e.message);
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

    $.ajax({
        type: "POST",
        url: URL__CALENDAR_VIEW,
        data: payload
    })
    .done(function (server_response) {
        if (server_response['result_success'] == 'pass') {
            calendar_table.ajax.reload( );
            calendar_end_date = new Date(server_response['calendar_end_date']);
            calendar_final_balance = server_response['final_balance']
        } else {
            user_message('fail', server_response['result_message']);
        }
    });
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

var calendar_search = function( return_from_server, search_direction ) {
    var search_term = $('#txt__calendar_search').val();
    var found_term = false;
    var highlight_exists = false;
    var found_highlight = false;
    var $first_row = $('#table__calendar > tbody');

    // Find any currently highlighted row and start the search from there
    if ($('#table__calendar').find('td.highlight').length) {
        highlight_exists = true;
    }

    // If the search term is in the current payment list, highlight the row
    $tr_list = (search_direction == 'forwards') ? $('#table__calendar > tbody').children('tr') : $('#table__calendar > tbody').children('tr').reverse();
    $tr_list.each( function () {
        if (highlight_exists && !found_highlight) {
            if ($(this).children('td.highlight').length) {
                found_highlight = true;
                $(this).children('td').removeClass( 'highlight' );
                console.info('calendar_search:- found highlighted row: ' + $(this).data('row_id'));
            }
        } else if (!highlight_exists || found_highlight) {
            $(this).children('td.calendar__searchable').each( function () {
                var cell_text =  $(this).text();
                if (cell_text.toLowerCase().indexOf(search_term.toLowerCase()) > -1) {
                    var $match_row = $(this).parent('tr');
                    $match_row.children('td').addClass( 'highlight' );
                    found_term = true;
                    $match_row.scrollToPayment();
                    calendar_selected_row_id = $match_row.data('row_id');
                    console.info('calendar_search:- calendar_selected_row_id: ' + calendar_selected_row_id)
                    return false;
                }
            });
            if (found_term) {
                return false;
            }
        }
    });

    // Otherwise check the payments in the db
    if (!found_term && !return_from_server && search_direction == 'forwards') {
        var new_calendar_start_date = moment(calendar_end_date).add(1, 'd');
        if (typeof calendar_final_balance === 'undefined') {
//            user_message('fail', 'calendar_final_balance not defined');
            return false;
        }

        var payload = "action=search&search_term=" + search_term
                        + '&start_date=' + moment(new_calendar_start_date).format('YYYY-MM-DD')
                        + '&end_date=' + moment(new_calendar_start_date).format('YYYY-MM-DD')
                        + '&final_balance=' + calendar_final_balance;
        $.ajax({
                type: "POST",
                url: URL__CALENDAR_VIEW,
                data: payload
            })
            .done(function (server_response) {
                if (server_response['result_success'] == 'pass') {
                    calendar_table.rows.add(server_response['data']).draw();
                    calendar_end_date = new Date(server_response['calendar_end_date']);
                    calendar_final_balance = server_response['final_balance']
                    calendar_search( true, 'forwards' );
                } else {
                    user_message('fail', server_response['result_message']);
                }
            });
    }

    // Otherwise error message
}

var deletePayment = function() {
    var payment_id = $(this).closest('tr').data('payment_id');
    var payment_title = $(this).closest('tr').children('td.calendar__title').text();
    var dialog_html = '<div id="dialog" name="dialog"><div class="ui-icon ui-icon-alert" style="margin-top: 20px;margin-left: 20px;position: relative;float: left;"></div>'
                        + '<div style="margin-top: 20px;position: relative;float: right;width: 80%;">Are you sure you want to delete "' + payment_title + '"?</div></div>'
    $(this).append(dialog_html);
    $( "#dialog" ).dialog({
        dialogClass: "dialog-no-titlebar",
        position: { my: "left top", at: "left top", of: $(this) },
        buttons: [
           {
                text: "OK",
                click: function() {
                    var payload = "action=delete&payment_id=" + payment_id
                                    + '&start_date=' + moment(calendar_start_date).format('YYYY-MM-DD')
                                    + '&end_date=' + moment(calendar_end_date).format('YYYY-MM-DD');
                    $.ajax({
                            type: "POST",
                            url: URL__UPDATE_PAYMENT,
                            data: payload
                        })
                        .done(function (server_response) {
                            user_message(server_response['result_success'], server_response['result_message']);
                            refresh_calendar_search_terms(server_response['search_terms']);
                            if (server_response['result_success'] === 'pass') reloadCalendar();
                        });
                $( this ).dialog( "close" );
                }
            },
            {
                text: "Cancel",
                click: function() {
                $( this ).dialog( "close" );
                }
            }
        ],
        modal: true
        });
}

var reset_editing_state = function() {
    //console.debug('reset_editing_state:- looking...');
    $('.payment_edit_cancel').each(function() {
        console.debug('reset_editing_state:- resetting ' + $(this).prop('tagName') + ': ' + $(this).attr('id')
            + '/' + $(this).attr('class'));
        $(this).click()
    });
}

var updateCalendarSettingsForDate = function (event) {
    if ($('#form__payment_detail input[name="rdo__series_choice"]').val() == 'this') {
        return false;
    }

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
}

var validate_schedule_fields = function () {
    var error_message = '';

    if ($("input[name='radio__until']:checked").val() == 'until_end_date'
            && $('#id_end_date').datepicker('getDate') < $('#id_next_date').datepicker('getDate')) {
        error_message = 'Until date must be after Next Payment date';
    }

    // Can't link to itself
    if ($('.select__schedule_frequency option:selected').text() == "Linked to Other Payment"
            && $('#id_linked_to').val() == $('#id_payment_id').val() ) {
        error_message = 'Payment cannot be linked to itself';
    }

    return error_message;
}