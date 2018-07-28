//THIS FILE MUST BE IMPORTED BEFORE THE "main" FILE.

var processManageCategories = function(payload)  {
    var jqxhr = $.ajax({
            method: "POST",
            url: URL__MANAGE_CATEGORIES,
            data: payload
        })
        .done(function(server_response) {
            if (server_response['result_success'] == 'fail') {
                user_message('fail', server_response['result_message']);
                return false;
            }

            // update was successful and new html for updated combos received
            var selected_payment_type;
            var selected_category;
            var selected_subcategory;
            $edit_row = $('.tr__calendar_inline_edit_row');
            new_row = '<td colspan="' + ($edit_row.prev('tr').children('td').length) + '">';
            new_row += server_response;
            new_row += '</td>';
            if ($('.tr__calendar_inline_manage_categories').length == 0) {
                $edit_row.after('<tr class="tr__calendar_inline_manage_categories">' + new_row + '</tr>');
            } else {
                $('.tr__calendar_inline_manage_categories').html(new_row);
            }
            $('#div__calendar').animate({
                scrollTop: ($('#div__calendar').scrollTop()
                            + $('.tr__category_update').offset().top
                            + $('.tr__category_update').height()
                            - $('#div__calendar').offset().top
                            - $('#div__calendar').height()) + 'px'
            }, 'fast');

            // initialise UI
            $('.button__manage_categories_payment_types_delete')
                .button( {
                    icons: { primary: 'ui-icon-trash', secondary: null },
                    text: false
                })
                .click(_.debounce(function() { deleteCategory($(this), 'payment_type'); }, MILLS_TO_IGNORE_CLICKS, true));
            $('.button__manage_categories_categories_delete')
                .button( {
                    icons: { primary: 'ui-icon-trash', secondary: null },
                    text: false
                })
                .click(_.debounce(function() { deleteCategory($(this), 'category'); }, MILLS_TO_IGNORE_CLICKS, true));
             $('.button__manage_categories_subcategories_delete')
                .button( {
                    icons: { primary: 'ui-icon-trash', secondary: null },
                    text: false
                })
                .click(_.debounce(function() { deleteCategory($(this), 'subcategory'); }, MILLS_TO_IGNORE_CLICKS, true));

            // default in categories
            $('#id__manage_categories_payment_types tr').each( function () {
                if ($(this).children(':first').text() == $('#id_selected_payment_type').val()) {
                    $(this).children('td').addClass('highlighted');
                    selected_payment_type = $('#id_selected_payment_type').val();
                } else {
                    $(this).children('td').removeClass('highlighted');
                }
                if ($(this).children(':first').text() == $('#id_updated_payment_type').val()) {
                    selectCategories($(this), 'payment_type');
                    selected_payment_type = $('#id_updated_payment_type').val();
                }
            });
            $('#id__manage_categories_categories tr').each( function () {
                if ($(this).children(':first').text() == $('#id_selected_category').val()) {
                   $(this).children('td').addClass('highlighted');
                   selected_category = $('#id_selected_category').val();
                } else {
                    $(this).children('td').removeClass('highlighted');
                }
                if ($(this).children(':first').text() == $('#id_updated_category').val()) {
                   selectCategories($(this), 'category');
                   selected_category = $('#id_updated_category').val();
                }
            });
            $('#id__manage_categories_subcategories tr').each( function () {
                if ($(this).children(':first').text() == $('#id_selected_subcategory').val()) {
                    $(this).children('td').addClass('highlighted');
                    selected_subcategory = $('#id_selected_subcategory').val();
                } else {
                    $(this).children('td').removeClass('highlighted');
                }
                if ($(this).children(':first').text() == $('#id_updated_subcategory').val()) {
                    selectCategories($(this), 'subcategory');
                    selected_subcategory = $('#id_updated_subcategory').val();
                }
            });

            // Update combos in Update Payment form
            if ($('#form__payment_detail').length) {
                updatePaymentFormCategoryCombos('payment_type', selected_payment_type);
                updatePaymentFormCategoryCombos('category', selected_category);
                updatePaymentFormCategoryCombos('subcategory', selected_subcategory);
            }

            // Update payments in calendar
            for (var i = 0; i < updated_payments.length; i++) {
                $('tr[data-payment_id="' + updated_payments[i].payment_id + '"]')
                        .find('div.calendar__payment_classification').replaceWith( function() {
                    var row = new Object();
                    row.payment_type_id = updated_payments[i].payment_type_id;
                    row.category_id = updated_payments[i].category_id;
                    row.category = updated_payments[i].category;
                    row.subcategory_id = updated_payments[i].subcategory_id;
                    row.subcategory = updated_payments[i].subcategory;
                    return render_category( updated_payments[i].payment_type, '', row);
                });
            }
        });
}


function initManageCategories(categorymap) {
    // validate
    jQuery.validator.addMethod("existingEntry", function(value, element, params) {
        return $('#form__manage_categories').find('#' + params + ' option').filter(function () { return $(this).html().toLowerCase() == value.toLowerCase(); }).length == 0;
    }, 'New entry must be unique');

    $('#form__manage_categories')
        .submit(function(event) {
            event.preventDefault();
        })
        .validate({
            highlight: function(element, errorClass, validClass) {
                $(element.form).find("label[for=" + element.id + "]").parent().removeClass(validClass).addClass(errorClass);
            },
            unhighlight: function(element, errorClass, validClass) {
                $(element.form).find("label[for=" + element.id + "]").parent().removeClass(errorClass).addClass(validClass);;
            },
            ignore: 'select'    // don't validate the lists themselves
        });

    // hook up events
    $('#id__manage_categories_payment_types tr td:first-child').click(_.debounce(function() { selectCategories($(this).parent(), 'payment_type') }, MILLS_TO_IGNORE_CLICKS, true));
    $('#id__manage_categories_categories tr td:first-child').click(_.debounce(function() { selectCategories($(this).parent(), 'category') }, MILLS_TO_IGNORE_CLICKS, true));
    $('#id__manage_categories_subcategories tr td:first-child').click(_.debounce(function() { selectCategories($(this).parent(), 'subcategory') }, MILLS_TO_IGNORE_CLICKS, true));

    $('#button__payment_type_add').button( {
            icons: { primary: 'ui-icon-plus', secondary: null },
            text: false
        })
        .click(_.debounce(function() {
            var pt_no = 1;
            var pt_name = 'Payment Type #' + pt_no;
            while ($('#id__manage_categories_payment_types td:contains("' + pt_name + '")').length > 0) {
                pt_no += 1;
            }
            processManageCategories( { 'new_payment_type' : pt_name } );
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__category_add').button( {
            icons: { primary: 'ui-icon-plus', secondary: null },
            text: false
        })
        .click(_.debounce(function(){
            if ($('#id__manage_categories_payment_types td.selected').parent().length != 1) {
                user_message('fail', 'Create Category failed. Please select a Payment Type for the new Category');
                return false;
            }
            var cat_no = 1;
            var cat_name = 'Category #' + cat_no;
            while ($('#id__manage_categories_categories td:contains("' + cat_name + '")').length > 0) {
                cat_no += 1;
            }
            processManageCategories( { 'payment_type' : $('#id__manage_categories_payment_types td.selected').parent().data('payment_type_id'),
                'new_category' : cat_name } );
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__subcategory_add').button( {
            icons: { primary: 'ui-icon-plus', secondary: null },
            text: false
        })
        .click(_.debounce(function(){
            if ($('#id__manage_categories_categories td.selected').parent().length != 1) {
                user_message('fail', 'Create Subcategory failed. Please select a Category for the new Subcategory');
                return false;
            }
            var subcat_no = 1;
            var subcat_name = 'Subcategory #' + subcat_no;
            while ($('#id__manage_categories_subcategories td:contains("' + subcat_name + '")').length > 0) {
                subcat_no += 1;
            }
            processManageCategories( { 'category' : $('#id__manage_categories_categories td.selected').parent().data('category_id'),
                'new_subcategory' : subcat_name } );
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__payment_type_update').button( {
            icons: { primary: 'ui-icon-check', secondary: null },
            text: false
        })
        .click(_.debounce(function(){
            if ($('#id__manage_categories_payment_types td')
                    .filter(function() { return $(this).text() === $('#txt__payment_type_update').val(); })
                    .length != 0) {
                user_message('fail', 'Update Payment Type failed. Payment Type "' + $('#txt__payment_type_update').val() +'" already exists.');
                $('#txt__payment_type_update').select();
                return false;
            }
            processManageCategories( {
                'edit_payment_type_id' : $('#id__manage_categories_payment_types td.selected').parent().data('payment_type_id'),
                'edit_payment_type_name' : $('#txt__payment_type_update').val()
            } );
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__category_update').button( {
            icons: { primary: 'ui-icon-check', secondary: null },
            text: false
        })
        .click(_.debounce(function(){
            if ($('#id__manage_categories_categories td')
                    .filter(function() { return $(this).text() === $('#txt__category_update').val(); })
                    .length != 0) {
                user_message('fail', 'Update Category failed. Category "' + $('#txt__category_update').val() +'" already exists.');
                $('#txt__category_update').select();
                return false;
            }
            processManageCategories( {
                'edit_category_id' : $('#id__manage_categories_categories td.selected').parent().data('category_id'),
                'edit_category_name' : $('#txt__category_update').val()
            } );
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__subcategory_update').button( {
            icons: { primary: 'ui-icon-check', secondary: null },
            text: false
        })
        .click(_.debounce(function(){
            if ($('#id__manage_categories_subcategories td')
                    .filter(function() { return $(this).text() === $('#txt__subcategory_update').val(); })
                    .length != 0) {
                user_message('fail', 'Update Subcategory failed. Subcategory "' + $('#txt__subcategory_update').val() +'" already exists.');
                $('#txt__subcategory_update').select();
                return false;
            }
            processManageCategories( {
                'edit_subcategory_id' : $('#id__manage_categories_subcategories td.selected').parent().data('subcategory_id'),
                'edit_subcategory_name' : $('#txt__subcategory_update').val()
            } );
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__payment_type_cancel').button( {
            icons: { primary: 'ui-icon-close', secondary: null },
            text: false
        })
        .click(_.debounce(function() {
            $('#txt__payment_type_update').val('').select();
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__category_cancel').button( {
            icons: { primary: 'ui-icon-close', secondary: null },
            text: false
        })
        .click(_.debounce(function() {
            $('#txt__category_update').val('').select();
        }, MILLS_TO_IGNORE_CLICKS, true));
    $('#button__subcategory_cancel').button( {
            icons: { primary: 'ui-icon-close', secondary: null },
            text: false
        })
        .click(_.debounce(function() {
            $('#txt__subcategory_update').val('').select();
        }, MILLS_TO_IGNORE_CLICKS, true));
//    $('#button__delete_payment_type').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));
//    $('#button__delete_category').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));
//    $('#button__delete_subcategory').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));

    $('#button__manage_categories_done').button().click(_.debounce(manageCategoriesDone,MILLS_TO_IGNORE_CLICKS, true));

    $('.tr__category_update input').keyup(function(event) {
        if (event.keyCode == 13) {
            $(this).siblings('.button__update').click();
            event.preventDefault();
        }
        if (event.keyCode == 27) {
            $(this).siblings('.button__cancel').click();
            event.preventDefault();
        }
    });
}

function updateCategoryValues() {
    var payload;
//    if(!$('#form__manage_categories').validate().valid()) {
//        console.info("updateCategoryValues:- form invalid");
//        return;
//    }

    switch($(this).attr('id')) {
        case 'button__payment_type_update':
            if ($(this).text() == 'Add') {
                payload = { 'new_payment_type' : $('#txt__payment_type_update').val() }
            } else {
                payload = {
                    'edit_payment_type_id' : $('#id__manage_categories_payment_type td.selected').data('payment_type_id'),
                    'edit_payment_type_name' : $('#txt__payment_type_update').val()
                }
            }
            break;
        case 'button__category_update':
            if ($(this).text() == 'Add') {
                if (!$('.mc_payment_type').val() || $('.mc_payment_type').val().length > 1) {
                    showErrorMessage('Please select a single payment type');
                } else {
                    payload = { 'payment_type' : $('.mc_payment_type').find('option:selected').val()
                        , 'new_category' : $('#txt__category_update').val() }
                }
            } else {
                payload = {
                    'edit_category_id' : $('.mc_category').find('option:selected').val(),
                    'edit_category_name' : $('#txt__category_update').val()
                }
            }
            break;
        case 'button__subcategory_update':
            if ($(this).text() == 'Add') {
                if (!$('.mc_category').val() || $('.mc_category').val().length > 1) {
                    showErrorMessage('Please select a single category');
                }
                else {
                    payload = { 'category' : $('.mc_category').find('option:selected').val()
                        , 'new_subcategory' : $('#txt__subcategory_update').val()}
                }
            } else {
                payload = {
                    'edit_subcategory_id' : $('.mc_subcategory').find('option:selected').val(),
                    'edit_subcategory_name' : $('#txt__subcategory_update').val()
                }
            }
            break;
        case 'button__delete_payment_type':
            if (window.confirm("Are you sure you want to delete payment type " + $('.mc_payment_type').find('option:selected').text() + "?")) {
                payload = { 'delete_payment_type' : $('.mc_payment_type').find('option:selected').val()}
            }
            break;
        case 'button__delete_category':
            if (window.confirm("Are you sure you want to delete category " + $('.mc_category').find('option:selected').text() + "?")) {
                payload = { 'delete_category' : $('.mc_category').find('option:selected').val()}
            }
            break;
        case 'button__delete_subcategory':
            if (window.confirm("Are you sure you want to delete subcategory " + $('.mc_subcategory').find('option:selected').text() + "?")) {
                payload = { 'delete_subcategory' : $('.mc_subcategory').find('option:selected').val()}
            }
            break;
    }

    if (payload) {
        processManageCategories(payload);
    }
};

var showErrorMessage = function(error_message) {
    user_message('fail', error_message);
}

var updatePaymentFormCategoryCombos = function(which_combo, selection_text) {
    console.debug('updatePaymentFormCategoryCombos:- which_combo: "' + which_combo + '", selection_text: "' + selection_text + '"');
    var select__which_combo = $('#form__payment_detail #id_' + which_combo);
    var curr_selection;
    var which_combos;
    switch(which_combo) {
        case 'payment_type':
            which_combos = 'payment_types';
            break;
        case 'category':
            which_combos = 'categories';
            break;
        case 'subcategory':
            which_combos = 'subcategories';
            break;
    }
    if (typeof selection_text === 'undefined' || selection_text === 'None' || selection_text === '') {
        curr_selection = select__which_combo.val();
    } else {
        if ($('#id__manage_categories_' + which_combos +' td.selected').parent().length === 1) {
            curr_selection = $('#id__manage_categories_' + which_combos +' td.selected').parent().data(which_combo + '_id');
        } else if ($('#id__manage_categories_' + which_combos +' td.highlighted').parent().length === 1) {
            curr_selection = $('#id__manage_categories_' + which_combos +' td.highlighted').parent().data(which_combo + '_id');
        } else {
            console.debug('updatePaymentFormCategoryCombos:- Please select a single ' + which_combo + ', selection_text: "' + selection_text + '" (' + typeof selection_text + ')');
            console.debug('updatePaymentFormCategoryCombos:- highlighted parents: ' + $('#id__manage_categories_' + which_combos +' td.highlighted').parent().length);
            user_message('fail', 'Please select a single ' + which_combo + ', selection_text: "' + selection_text + '" (' + typeof selection_text + ')');
            return false;
        }
    }
    select__which_combo.empty();
    $('#id__manage_categories_' + which_combos +' tr td:first-child').each( function() {
        select__which_combo.append($("<option></option>")
            .val($(this).parent().data(which_combo + '_id'))
            .text($(this).text()));
    });
    select__which_combo.val(curr_selection);
    select__which_combo.trigger("chosen:updated");
//    select__which_combo.change();
}

var manageCategoriesDone = function() {
    $('.tr__calendar_inline_manage_categories').remove();
    if ($('.tr__calendar_inline_edit_row').html() === '') $('.tr__calendar_inline_edit_row').remove();
}

var selectCategories = function($this, which_category) {
    console.debug('selectCategories:- $this: "' + $this.children(':first').text() + '", which_category: "' + which_category + '"');
    // if choosing a new parent
    if ((which_category === 'payment_type' && $('#id__manage_categories_categories td.selected').parent().length === 1)
            || (which_category === 'category' && $('#id__manage_categories_subcategories td.selected').parent().length === 1)) {
        $this.siblings().andSelf().addClass('selected');
        var parent_type;
        var child_type;
        var child_name;
        var payload;
        if (which_category === 'payment_type') {
            parent_type =  'Payment Type';
            child_type = 'Category';
            child_name = $('#id__manage_categories_categories td.selected:first').text();
            payload = 'new_payment_type_for_category=' + $this.data('payment_type_id')
                    + '&category_id=' + $('#id__manage_categories_categories td.selected').parent().data('category_id');
        } else {
            parent_type = 'Category';
            child_type = 'Subcategory';
            child_name = $('#id__manage_categories_subcategories td.selected:first').text();
            payload = 'new_category_for_subcategory=' + $this.data('category_id')
                    + '&subcategory_id=' + $('#id__manage_categories_subcategories td.selected').parent().data('subcategory_id');
        }
        var dialog_html = '<div id="dialog" name="dialog"><div class="ui-icon ui-icon-info" style="margin-top: 20px;margin-left: 20px;position: relative;float: left;"></div>'
                        + '<div style="margin-top: 20px;position: relative;float: right;width: 80%;">Do you want to update the '
                        + parent_type + ' of "' + child_name + '" to "' + $this.children(':first').text() + '"?</div></div>'
        $this.append(dialog_html);
        $( "#dialog" ).dialog({
            dialogClass: "dialog-no-titlebar",
            position: { my: "left top", at: "right top", of: $this },
            buttons: [
                {
                    text: "OK",
                    click: function() {
                        processManageCategories(payload);
                        $(this).dialog( "close" );
                        return false;
                    }
                },
                {
                    text: "Cancel",
                    click: function() {
                        $(this).dialog( "close" );
                    }
                }
            ],
            modal: true
            });
    }

    $('#id__manage_categories_payment_types td').each(function() { $(this).removeClass('highlighted'); $(this).removeClass('selected'); });
    $('#id__manage_categories_categories td').each(function() { $(this).removeClass('highlighted'); $(this).removeClass('selected'); });
    $('#id__manage_categories_subcategories td').each(function() { $(this).removeClass('highlighted'); $(this).removeClass('selected'); });
    $this.children('td').addClass('selected');
    $('#txt__payment_type_update').val((which_category === 'payment_type') ? $this.children(':first').text() : '');
    $('#txt__category_update').val((which_category === 'category') ? $this.children(':first').text() : '');
    $('#txt__subcategory_update').val((which_category === 'subcategory') ? $this.children(':first').text() : '');
    for (i = 0; i < categorymap.length; i++) {
        if (which_category === 'payment_type' && $this.data('payment_type_id') == categorymap[i][0]) {
            if (typeof(categorymap[i][1]) !== 'undefined') {
                $('#id__manage_categories_categories tr').each(function() { if ($(this).data('category_id') == categorymap[i][1]) $(this).children('td').addClass('highlighted'); });
            }
            if (typeof(categorymap[i][2]) !== 'undefined') {
                $('#id__manage_categories_subcategories tr').each(function() { if ($(this).data('subcategory_id') == categorymap[i][2]) $(this).children('td').addClass('highlighted'); });
            }
        }
        if (which_category === 'category' && $this.data('category_id') == categorymap[i][1]) {
            $('#id__manage_categories_payment_types tr').each(function() { if ($(this).data('payment_type_id') == categorymap[i][0]) $(this).children('td').addClass('highlighted'); });
            if (typeof(categorymap[i][2]) !== 'undefined') {
                $('#id__manage_categories_subcategories tr').each(function() { if ($(this).data('subcategory_id') == categorymap[i][2]) $(this).children('td').addClass('highlighted'); });
            }
        }
        if (which_category === 'subcategory' && $this.data('subcategory_id') == categorymap[i][2]) {
            $('#id__manage_categories_payment_types tr').each(function() { if ($(this).data('payment_type_id') == categorymap[i][0]) $(this).children('td').addClass('highlighted'); });
            $('#id__manage_categories_categories tr').each(function() { if ($(this).data('category_id') == categorymap[i][1]) $(this).children('td').addClass('highlighted'); });
        }
        $('#txt__' + which_category + '_update').select();
    }
}

var deleteCategory = function ($this, which_combo) {
    var dialog_html = '<div id="dialog" name="dialog"><div class="ui-icon ui-icon-alert" style="margin-top: 20px;margin-left: 20px;position: relative;float: left;"></div>'
                    + '<div style="margin-top: 20px;position: relative;float: right;width: 80%;">Are you sure you want to delete '
                    + '"' + $this.closest('tr').children(':first-child').text() + '"?</div></div>'
    $this.append(dialog_html);
    $( "#dialog" ).dialog({
        dialogClass: "dialog-no-titlebar",
        position: { my: "left top", at: "right top", of: $this },
        buttons: [
            {
                text: "OK",
                click: function() {
                    var payload = new Object();
                    payload['delete_' + which_combo] = $this.closest('tr').data(which_combo + '_id');
                    processManageCategories(payload);
                    $(this).dialog( "close" );
                    return false;
                }
            },
            {
                text: "Cancel",
                click: function() {
                    $(this).dialog( "close" );
                }
            }
        ],
        modal: true
        });
}