var tbl__upload_table;
var trans_table__default_headers = [['Row Number','Date','Description','Credit','Debit','Balance']];
var trans_table_opt__header_row = true;

var initFileUpload = function(transactions_rows, has_header) {
    // Initialise UI
    $('#id_account').chosen();
    $('#btn__upload_file_submit').button()
        .click(_.debounce(uploadFile, MILLS_TO_IGNORE_CLICKS, true));

    console.info('initFileUpload:- has_header: ' + has_header);
    trans_table_opt__header_row = (has_header === 'True') ? true : false;
    $('#chk__header_row').prop('checked', trans_table_opt__header_row)
        .checkboxradio()
        .bind('change', function(){
            trans_table_opt__header_row = $(this).is(':checked');
            toggleHeaderRow();
        });

    initUploadTable(transactions_rows);
}

var uploadFile = function() {
    var frm = $('#frm_file_upload');
    frm.submit(function () {
        $.ajax({
            type: frm.attr('method'),
            url: URL__FILE_UPLOAD,
            data: new FormData(frm[0]),
            processData: false,
            contentType: false,
            success: function (serverResponse_data) {
                user_message(serverResponse_data['result_success'], serverResponse_data['result_message']);
                trans_table_opt__header_row = serverResponse_data['has_header'];
                console.info('uploadFile:- serverResponse_data[has_header]: ' + serverResponse_data['has_header']
                    + ', trans_table_opt__header_row: ' + trans_table_opt__header_row);
                tbl__upload_table.destroy();
                $('#tbl__upload_table').empty();
                buildUploadTable(serverResponse_data['transactions_rows']);
            },
            error: ajaxErr
        });
        return false;
    });
}

var initUploadTable = function(transactions_rows) {
    // Load previous upload if available
    if (transactions_rows.length !== 0) {
        buildUploadTable(transactions_rows);
    } else {
        // Empty table
        buildUploadTable(trans_table__default_headers);
    }
}

var buildUploadTable = function( row_data ) {
    var ary_header = [];
    var cols_header = [];

    if (trans_table_opt__header_row) {
        ary_header = row_data.shift();
        for (i = 0; i < ary_header.length; i++) {
            var new_header = { title: String(ary_header[i]) };
            cols_header.push(new_header);
        }

    } else {
        for (i = 0; i < row_data[0].length; i++) {
            var new_header = { title: ((i === 0) ? 'Row Number' : 'Column ' + i) };
            cols_header.push(new_header);
        }
    }

    tbl__upload_table = $('#tbl__upload_table').DataTable( {
        fixedHeader: true,
        columnDefs: [ {
            targets: 'hide-in-compact',
            visible: true
        } ],
        data: row_data,
        columns: cols_header,
        initComplete: uploadTableLoadComplete
    } );
}

var uploadTableLoadComplete = function(settings, json) {
    console.info('uploadTableLoadComplete:- entering, transactions_rows.length: ' + transactions_rows.length);
    // Add header row for column-type indicators
    if (transactions_rows.length === 0) return;

    var ind_header = $('<tr />');
//    var ind_columns = [];
    for (i=0; i < settings.aoColumns.length; i++ ) {
//        console.info('uploadTableLoadComplete:- settings.aoColumns[' + i + '].sTitle: ' + settings.aoColumns[i].sTitle);
        if (fields_payment_date == i) {
            ind_header.append( $('<th />', { class: 'th__ind_header' }).append( $('<div />', { text: 'Date', class: 'div__ind_header_date div__ind_header_button'}) ));
        } else if (fields_description == i) {
            ind_header.append( $('<th />', { class: 'th__ind_header' }).append( $('<div />', { text: 'Description', class: 'div__ind_header_description div__ind_header_button'}) ));
        } else if (fields_incoming == i || fields_outgoing == i) {
            var amount_field = $('<th />', { class: 'th__ind_header' });
            if (fields_incoming == i) {
                amount_field.append( $('<div />', { text: 'Incoming', class: 'div__ind_header_incoming div__ind_header_button'}) );
            }
            if (fields_outgoing == i) {
                if (amount_field == undefined ) {
                    amount_field.append( $('<div />', { text: 'Outgoing', class: 'div__ind_header_outgoing div__ind_header_button'}) );
                } else {
                    amount_field.append( $('<div />', { text: 'Outgoing', class: 'div__ind_header_outgoing div__ind_header_button'}) );
                }
            }
            ind_header.append(amount_field);
        } else {
            ind_header.append( $('<th />', { class: 'th__ind_header' }) );
        }
    }
    $('#tbl__upload_table thead').prepend(ind_header);
    $( ".th__ind_header" ).droppable( "option", "accept", ".div__ind_header_button" );
}

var toggleHeaderRow = function() {
    if (typeof(tbl__upload_table) === 'undefined') return;
    console.info('toggleHeaderRow :- tbl__upload_table.rows().data()[0]: "' + tbl__upload_table.rows().data()[0]
        + '", trans_table_opt__header_row: ' + trans_table_opt__header_row);

    if (trans_table_opt__header_row) {
        var curr_header = [];
        console.info('toggleHeaderRow :- tbl__upload_table.rows().indexes()[0]: ' + tbl__upload_table.rows().indexes()[0]
            + ', tbl__upload_table.rows(tbl__upload_table.rows().indexes()[0]).data()[0]: ' + tbl__upload_table.rows(tbl__upload_table.rows().indexes()[0]).data()[0]);
        var first_row_index = tbl__upload_table.rows().indexes()[0];
        var first_row = tbl__upload_table.rows(first_row_index).data()[0];
        for (i = 0; i < first_row.length; i++) {
            $( tbl__upload_table.column(i).header() ).text(first_row[i]);
        }
        tbl__upload_table.rows(first_row_index).remove(curr_header).draw();

    } else {
        var curr_header = [];
        for (i = 0; i < tbl__upload_table.columns().header().length; i++) {
            curr_header.push( $(tbl__upload_table.column(i).header() ).text());
            $( tbl__upload_table.column(i).header() ).text( (i === 0) ? 'Row Number' : 'Column ' + i);
        }
        console.info('toggleHeaderRow :- curr_header: ' + curr_header);
        tbl__upload_table.row.add(curr_header).draw(false);
        tbl__upload_table.order([0, 'asc']).draw();
    }
    console.info('toggleHeaderRow :- curr trans_table_opt__header_row: ' + trans_table_opt__header_row);
    trans_table_opt__header_row = !trans_table_opt__header_row;
    console.info('toggleHeaderRow :- new trans_table_opt__header_row: ' + trans_table_opt__header_row);
}