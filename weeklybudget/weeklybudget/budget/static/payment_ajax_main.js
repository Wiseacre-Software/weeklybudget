//THIS MUST BE IMPORTED AS THE VERY LAST THING BEFORE THE CLOSE </body>
//tag.



/**
   The Ajax "main" function. Attaches the listeners to the elements on
   page load
 */

var payments_table;

$(document).ready(function()  {
    $('#button__add_payment')
        .button()
        .click(_.debounce(processUpdatePayment, MILLS_TO_IGNORE_CLICKS, true));

    $('#button__toggle_calendar')
        .button()
        .click(_.debounce(togglePane, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__toggle_payments')
        .button()
        .click(_.debounce(togglePane, MILLS_TO_IGNORE_CLICKS, true));
//    $('.img__divider').click(_.debounce(togglePane, MILLS_TO_IGNORE_CLICKS, true));
    $('.payments_pane').hide( 'slide' );

    $('.col-divider').mouseover( function() {
            $(this).addClass("background-color-secondary-2-0");
        })
        .mouseleave( function() {
            $(this).removeClass("background-color-secondary-2-0");
        })
        .click(_.debounce(togglePane, MILLS_TO_IGNORE_CLICKS, true));

    // datatables
    $.fn.dataTable.moment( 'DD/MM/YYYY' );
//    payments_table = $('#table__payments').DataTable({
//        "columnDefs": [ {
//            "targets": 'hide-in-compact',
//            "visible": true
//        } ],
//        "ajax": {
//            method: "POST",
//            url: URL__GET_PAYMENTS
//        },
//        "columns": [
//            { data: 'payment_type' },
//            { data: 'category' },
//            { data: 'subcategory' },
//            { data: 'title' },
//            {
//                data: 'amount',
//                className: "money"
//            },
//            { data: 'in_out' },
//            {
//                data: 'frequency',
//                className: "dt-center"
//            },
//            {
//                data: 'next_date',
//                render: function ( data, type, row ) {
//                    return (moment(data).format("MMM D, YYYY"));
//                },
//                className: "dt-center"
//            },
//            {
//                data: 'payment_id',
//                render: function ( data, type, row ) {
//                    return ("<button class='button-update' data-payment_id='" + data + "'>Update</button>"
//                        + "<button class='button-delete' data-payment_id='" + data + "'>Delete</button>");
//                },
//                className: "dt-center"
//            }
//        ],
//        "order": [[ 0, 'asc' ], [ 1, 'asc' ], [ 3, 'asc' ]]
//    });
//
//    $('#table__payments').on( 'draw.dt', paymentListLoadComplete);
});

var paymentListLoadComplete = function( settings, json ) {
//            $('div.loading').remove();
    $('#table__payments .money').autoNumeric('init', {aSign: '$'});
    $('#table__payments .button-update')
        .button( {
            icons: { primary: 'ui-icon-pencil', secondary: null },
            text: false
        })
        .click(_.debounce(processUpdatePayment, MILLS_TO_IGNORE_CLICKS, true));
    $('#table__payments .button-delete')
        .button( {
            icons: { primary: 'ui-icon-trash', secondary: null },
            text: false
        })
        .click(_.debounce(processUpdatePayment, MILLS_TO_IGNORE_CLICKS, true));
}

var getPayments = function() {
    var jqxhr = $.ajax({
            method: "POST",
            url: URL__GET_PAYMENTS
        })
}

var togglePane = function(event) {
//    show_which_pane = ($('#button__toggle_calendar').text().indexOf('Show') > -1) ? 'calendar' : 'payments';
    show_which_pane = ($('.payments_pane').is(":visible")) ? 'calendar' : 'payments';
//    console.info('togglePane:- button: ' + $(this).prop('id') + ', show_which_pane: ' + show_which_pane);
    if (show_which_pane == 'calendar') {
        $('.calendar_pane').show( 'slide' );
        $('.payments_pane').hide( 'slide' );
        $("#img__calendar_view_toggle").attr("src", SRC__MOBILE_IMAGES + "/carat-l-black.png");
        $("#img__payments_view_toggle").attr("src", SRC__MOBILE_IMAGES + "/carat-u-black.png");
//        $('#button__toggle_calendar').button('option', 'label', 'Hide Calendar');
//        $('#button__toggle_payments').button('option', 'label', 'Show Payments');
    } else {
        $('.calendar_pane').hide( 'slide' );
        $('.payments_pane').show( 'slide' );
        $("#img__calendar_view_toggle").attr("src", SRC__MOBILE_IMAGES + "/carat-u-black.png");
        $("#img__payments_view_toggle").attr("src", SRC__MOBILE_IMAGES + "/carat-r-black.png");
//        $('#button__toggle_calendar').button('option', 'label', 'Show Calendar');
//        $('#button__toggle_payments').button('option', 'label', 'Hide Payments');
    }
}

// Custom validators
jQuery.validator.addMethod("defaultInvalid", function(value, element)
{
    return !(element.value == element.defaultValue);
}, 'This field is required');
