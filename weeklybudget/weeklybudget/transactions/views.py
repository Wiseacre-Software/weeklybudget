# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import logging
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie

from budget.models import BankAccount
from .models import *
from .forms import *
from .controller import *

logger = logging.getLogger(__name__)

@login_required
@ensure_csrf_cookie
def index(request):
    response_data = {}
    try:
        logger.debug('index:- entering')
        response_data['result_success'] = 'pass'

        response_data['form'] = UploadFileForm(request.user)

        if Extract.objects.filter(owner=request.user).exists():
            r = Extract.objects.filter(owner=request.user).order_by('-extract_run_id')[0]
            response_data['has_header'] = r.has_header_row
            response_data['fields_payment_date'] = r.fields_payment_date
            response_data['fields_description'] = r.fields_description
            response_data['fields_incoming'] = r.fields_incoming
            response_data['fields_incoming_sign'] = r.fields_incoming_sign
            response_data['fields_outgoing'] = r.fields_outgoing
            response_data['fields_outgoing_sign'] = r.fields_outgoing_sign

            transactions = []
            if r.status == 'new' :
                for row in Transaction.objects.filter(owner=request.user, run=r).all():
                    transactions.append([ row.row_number ] + row.raw_text.split(r.delimiter))
            response_data['transactions_rows'] = json.dumps(transactions, cls=DjangoJSONEncoder)

        return render_to_response('transactions/index.html', response_data)

    except Exception as e:
        error_message = '{ "Exception": "%s" }' % \
                        (e.messages if hasattr(e, 'messages') else e.message)
        logger.error(error_message)
        response_data['result_success'] = 'fail'
        response_data['result_message'] = error_message
        return HttpResponse(json.dumps(response_data, cls=DjangoJSONEncoder), content_type="application/json")

@login_required
@ensure_csrf_cookie
def upload_file(request):
    response_data = {}
    try:
        logger.debug('upload_file:- entering with content: %s' % (request.POST))

        if request.method == 'POST':
            response_data['result_message'] = 'Upload successful!'
            response_data['result_success'] = 'pass'

            form = UploadFileForm(request.user, request.POST, request.FILES)
            if not form.is_valid():
                raise ValidationError(form.errors.as_json())
            if not BankAccount.objects.filter(owner=request.user, id=request.POST['account']).exists():
                raise ValidationError('Specified account does not exist')

            run_id = handle_uploaded_file(request.FILES['file'], request.POST['account'], request.user)
            r = Extract.objects.get(owner=request.user, extract_run_id=run_id)
            response_data['has_header'] = r.has_header_row
            response_data['fields_payment_date'] = r.fields_payment_date
            response_data['fields_description'] = r.fields_description
            response_data['fields_incoming'] = r.fields_incoming
            response_data['fields_incoming_sign'] = r.fields_incoming_sign
            response_data['fields_outgoing'] = r.fields_outgoing
            response_data['fields_outgoing_sign'] = r.fields_outgoing_sign

            response_data['transactions_rows'] = []
            for row in Transaction.objects.filter(run=r).all():
                response_data['transactions_rows'].append([ row.row_number ] + row.raw_text.split(r.delimiter))

            logger.debug('upload_file:- response_data[has_header]: %s' % (response_data['has_header']))
            return HttpResponse(json.dumps(response_data, cls=DjangoJSONEncoder), content_type="application/json")
        else:
            form = UploadFileForm(request.user)
        return render(request, 'transactions/index.html', {'form': form})

    except Exception as e:
        error_message = '{ "Exception": "%s" }' % \
                        (e.messages if hasattr(e, 'messages') else e.message)
        logger.error(error_message)
        response_data['result_success'] = 'fail'
        response_data['result_message'] = error_message
        return HttpResponse(json.dumps(response_data, cls=DjangoJSONEncoder), content_type="application/json")
