//THIS FILE MUST BE IMPORTED BEFORE THE "main" FILE.

var processManageCategories = function(payload)  {
    console.info('processManageCategories: entering, payload: ' + payload);

    var jqxhr = $.ajax({
            method: "POST",
            url: URL__MANAGE_CATEGORIES,
            data: payload
        })
        .done(function(serverResponse_data) {
            try {
                var o = JSON.parse(serverResponse_data);
                if (o.Exception) {
                    showErrorMessage(o.Exception);
                }
            } catch (e) {
                // update was successful and new html for updated combos received
                $edit_row = $('.tr__calendar_inline_edit_row');
                new_row = '<td colspan="' + ($edit_row.prev('tr').children('td').length) + '">';
                new_row += serverResponse_data;
                new_row += '</td>';
                if ($('.tr__calendar_inline_manage_categories').length == 0) {
                    $edit_row.after('<tr class="tr__calendar_inline_manage_categories">' + new_row + '</tr>');
                } else {
                    $('.tr__calendar_inline_manage_categories').html(new_row);
                }

                // Update combos in Update Payment form
                updatePaymentFormCategoryCombos('payment_type');
                updatePaymentFormCategoryCombos('category');
                updatePaymentFormCategoryCombos('subcategory');
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

    // jquery-ui
//    $('#table__manage_categories select, #table__manage_categories label, #table__manage_categories option').addClass('ui-widget');
    $('#table__manage_categories button').button();

    // hook up events
    $('.mc_payment_type').change(function () {
//        hideUpdateFields();
        $('.mc_category option:selected').each(function() { $(this).prop('selected', false) });
        $('.mc_subcategory option:selected').each(function() { $(this).prop('selected', false) });
        for (i = 0; i < categorymap.length; i++) {
            $(this).find('option:selected').each(function() {
                if (categorymap[i][0] == $(this).val()) {
                    $('.mc_category option[value="' + categorymap[i][1] + '"]').prop('selected', true);
                    $('.mc_subcategory option[value="' + categorymap[i][2] + '"]').prop('selected', true);
                }
            })
        }
    });
    $('.mc_payment_type').dblclick(function(){showUpdateFields('payment_type',true)});

    $('.mc_category').change(function () {
//        hideUpdateFields();
        // select valid payment_type and subcategory for selected category
        $('.mc_payment_type option:selected').each(function() { $(this).prop('selected', false) });
        $('.mc_subcategory option:selected').each(function() { $(this).prop('selected', false) });
        for (i = 0; i < categorymap.length; i++) {
            $('.mc_category').find('option:selected').each(function() {
                if (categorymap[i][1] == $(this).val()) {
                    $('.mc_payment_type option[value="' + categorymap[i][0] + '"]').prop('selected', true);
                    $('.mc_subcategory option[value="' + categorymap[i][2] + '"]').prop('selected', true);
                }
            })
        }
    })
    $('.mc_category').dblclick(function(){showUpdateFields('category',true)});

    $('.mc_subcategory').change(function () {
//        hideUpdateFields();
        // select valid payment_type and category for selected category
        $('.mc_payment_type option:selected').each(function() { $(this).prop('selected', false) });
        $('.mc_category option:selected').each(function() { $(this).prop('selected', false) });
        for (i = 0; i < categorymap.length; i++) {
            $('.mc_subcategory').find('option:selected').each(function() {
                if (categorymap[i][2] == $(this).val()) {
                    $('.mc_payment_type option[value="' + categorymap[i][0] + '"]').prop('selected', true);
                    $('.mc_category option[value="' + categorymap[i][1] + '"]').prop('selected', true);
                }
            })
        }
    })
    $('.mc_subcategory option').dblclick(function(){showUpdateFields('subcategory',true)});

    $('#button__new_payment_type').click(_.debounce(function(){showUpdateFields('payment_type',false)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__new_category').click(_.debounce(function(){showUpdateFields('category',false)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__new_subcategory').click(_.debounce(function(){showUpdateFields('subcategory',false)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__edit_payment_type').click(_.debounce(function(){showUpdateFields('payment_type',true)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__edit_category').click(_.debounce(function(){showUpdateFields('category',true)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__edit_subcategory').click(_.debounce(function(){showUpdateFields('subcategory',true)},MILLS_TO_IGNORE_CLICKS, true));

    $('#button__payment_type_update').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__category_update').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__subcategory_update').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__delete_payment_type').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__delete_category').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__delete_subcategory').click(_.debounce(function(){updateCategoryValues.call(this)},MILLS_TO_IGNORE_CLICKS, true));

    $('#button__manage_categories_done').click(_.debounce(manageCategoriesDone,MILLS_TO_IGNORE_CLICKS, true));

    $('.tr__category_update input').keypress(function(event) {
        if (event.which == 13) {
            $(this).siblings('button')[0].click();
            event.preventDefault();
        }
    });

    // initialise UI
//    $('#id_payment_type option:first-child').attr("selected", "selected").change();
}

function hideUpdateFields() {
    $('#txt__payment_type_update').val('').hide();
    $('#button__payment_type_update').hide();
    $('#txt__category_update').val('').hide();
    $('#button__category_update').hide();
    $('#txt__subcategory_update').val('').hide();
    $('#button__subcategory_update').hide();
}

function showUpdateFields(which_field, is_edit) {
//    hideUpdateFields();
    if (which_field == 'payment_type') {
        $('#txt__payment_type_update').show().focus();
        $('#button__payment_type_update').show();
        if (is_edit) {
            var edit_val = payment_types[$('.mc_payment_type').find('option:selected').val()];
            $('#button__payment_type_update').button('option', 'label', 'Update');
            $('#txt__payment_type_update').val(edit_val);
            $('#txt__payment_type_update').select();
        }
    }
    else if (which_field == 'category') {
        $('#txt__category_update').show().focus();
        $('#button__category_update').show();
        if (is_edit) {
            var edit_val = categories[$('.mc_category').find('option:selected').val()];
            $('#button__category_update').button('option', 'label', 'Update');
            $('#txt__category_update').val(edit_val);
            $('#txt__category_update').select();
        }
    }
    else {
        $('#txt__subcategory_update').show().focus();
        $('#button__subcategory_update').show();
        if (is_edit) {
            var edit_val = subcategories[$('.mc_subcategory').find('option:selected').val()];
            $('#button__subcategory_update').button('option', 'label', 'Update');
            $('#txt__subcategory_update').val(edit_val);
            $('#txt__subcategory_update').select();
        }
    }
}

function updateCategoryValues() {
    var payload;

//    console.info("updateCategoryValues:- id: " + $(this).attr('id') + ", text: " + $(this).text());

    if(!$('#form__manage_categories').validate().valid()) {
        console.info("updateCategoryValues:- form invalid");
        return;
    }

    switch($(this).attr('id')) {
        case 'button__payment_type_update':
            if ($(this).text() == 'Add') {
                payload = { 'new_payment_type' : $('#txt__payment_type_update').val() }
            } else {
                payload = {
                    'edit_payment_type_id' : $('.mc_payment_type').find('option:selected').val(),
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
    $('#div__manage_categories__error_messages').show();
    $('#span__manage_categories__error_messages').text(error_message);
}

var updatePaymentFormCategoryCombos = function(which_combo) {
    var select__which_combo = $('#form__payment_detail #id_' + which_combo);
    var curr_selection = select__which_combo.val();
    select__which_combo.empty();
    $('#form__manage_categories #id_' + which_combo + ' option').each( function() {
        select__which_combo.append($("<option></option>")
            .val($(this).val())
            .html($(this).html()));
    })
    select__which_combo.val(curr_selection);
    select__which_combo.trigger("chosen:updated");
}

var manageCategoriesDone = function() {
    $('#manage_categories').html('');

//    var payment_id = $('#form__payment_detail').find('#payment_id').val();
//    updatePaymentAjax({ 'payment_id' : payment_id });
}

/////////////////////////////////////////////////////////////////////////////////////////////////////////

// Unused code

/////////////////////////////////////////////////////////////////////////////////////////////////////////

function initManageCategories__manual(categorymapstr) {
    // hide category and subcategory initially
//    toggleManageCategoryFields('both', false);
//    var categorymap = categorymapstr.split(";");

    // hook up events
    $('#id_payment_type').change(function () {
//        alert($(this).find('option:selected').text());
//        toggleManageCategoryFields('category', true);

        // rebuild category combo
        $('#id_category').empty();
        var oitems = [];
        for (c in categorymap) {
            var citems = categorymap[c].split(',');
//            alert('citems[0]: ' + citems[0] + ', $(this): ' + $(this).find('option:selected').text());
            if (citems[0] == $(this).find('option:selected').text()) {
                oitems.push(citems[1]);
            }
        }
        uoitems = _.uniq(oitems, false);
        $('#id_category').append('<option>--- Choose category ---</option>');
        for (o in uoitems) {
//            alert(uoitems[o]);
            $('#id_category').append($('<option/>', {
                text : uoitems[o]
            }));
        }
    })

    $('#id_category').change(function () {
//        alert($(this).find('option:selected').text());
//        toggleManageCategoryFields('subcategory', true);

        // rebuild category combo
        $('#id_subcategory').empty();
        var oitems = [];
        for (c in categorymap) {
            var citems = categorymap[c].split(',');
//            alert('citems[0]: ' + citems[0] + ', $(this): ' + $(this).find('option:selected').text());
            if (citems[1] == $(this).find('option:selected').text()) {
                oitems.push(citems[2]);
            }
        }
        uoitems = _.uniq(oitems, false);
        $('#id_subcategory').append('<option>--- Choose subcategory ---</option>');
        for (o in uoitems) {
//            alert(uoitems[o]);
            $('#id_subcategory').append($('<option/>', {
                text : uoitems[o]
            }));
        }
    })
}

function initManageCategories__full_rebuild(categorymap) {

    // hook up events
    $('.mc_payment_type').change(function () {
        hideUpdateFields();

        // rebuild category list for payment type selected
        //  1. create list of valid categories for selected payment type
        var valid_categories = [];
        for (i = 0; i < categorymap.length; i++) {
            if (categorymap[i][0] == $(this).find('option:selected').val()
                && $.inArray(categorymap[i][1],valid_categories) == -1) {
                valid_categories.push(categorymap[i][1]);
            }
        }
//        console.log('valid_categories:' + valid_categories);

        //  2. rebuild categories list
        $('.mc_category').empty()
        for (j = 0; j < valid_categories.length; j++) {
//            console.log('manage_categories[valid_categories[[' + j + ']]:' + categories[valid_categories[j]]);
            $('.mc_category').append($('<option>', {
                value: valid_categories[j],
                text: categories[valid_categories[j]]
            }));
        }
        if ($('.mc_category').children().length == 0) {
            $('.mc_category').append($('<option>', {
                value: -1,
                text: '--- No categories ---'
            }));

            // 3. clear subcategories
            $('.mc_subcategory').empty()
            $('.mc_subcategory').append($('<option>', {
                value: -1,
                text: '--- Select Category ---'
            }));
        }
        else {
            $('.mc_category option:first-child').attr("selected", "selected").change();
        }

    });

    $('.mc_category').change(function () {
        // rebuild subcategory list for category selected
        //  1. create list of valid subcategories for selected category
        var valid_subcategories = [];
        for (i = 0; i < categorymap.length; i++) {
            if (categorymap[i][1] == $(this).find('option:selected').val()
                && $.inArray(categorymap[i][2],valid_subcategories) == -1) {
                valid_subcategories.push(categorymap[i][2]);
            }
        }
        console.log('valid_subcategories:' + valid_subcategories);

        //  2. rebuild subcategories list
        $('.mc_subcategory').empty()
        for (j = 0; j < valid_subcategories.length; j++) {
            console.log('subcategories[valid_subcategories[[' + j + ']]:' + subcategories[valid_subcategories[j]]);
            $('.mc_subcategory').append($('<option>', {
                value: valid_subcategories[j],
                text: subcategories[valid_subcategories[j]]
            }));
        }
        if ($('.mc_subcategory').children().length == 0) {
            $('.mc_subcategory').append($('<option>', {
                value: -1,
                text: '--- No subcategories ---'
            }));
        }
        else {
            $('.mc_subcategory option:first-child').attr("selected", "selected").change();
        }
    })

    $('#button__edit_payment_type').click(_.debounce(function(){showUpdateFields('payment_type',true)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__new_payment_type').click(_.debounce(function(){showUpdateFields('payment_type',false)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__edit_category').click(_.debounce(function(){showUpdateFields('category',true)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__new_category').click(_.debounce(function(){showUpdateFields('category',false)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__edit_subcategory').click(_.debounce(function(){showUpdateFields('subcategory',true)},MILLS_TO_IGNORE_CLICKS, true));
    $('#button__new_subcategory').click(_.debounce(function(){showUpdateFields('subcategory',false)},MILLS_TO_IGNORE_CLICKS, true));

    $('#button__category_update').click(_.debounce(function(){updateCategoryValues.call(this, 'category')},MILLS_TO_IGNORE_CLICKS, true));

    // initialise UI
    $('#id_payment_type option:first-child').attr("selected", "selected").change();
}

