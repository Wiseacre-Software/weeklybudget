# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import csv
import dateparser
from datetime import datetime
import logging
import re

from django.db.models import Max
from django.utils.dateparse import parse_date, parse_datetime
from django.utils.translation import get_language

from budget.models import BankAccount
from .models import Transaction, Extract

logger = logging.getLogger(__name__)

# region Methods

def handle_uploaded_file(f, account_id, user):
    try:
        logger.debug('handle_uploaded_file:- entering with file: %s' % (f.name))
        if not Extract.objects.filter(owner=user).exists():
            run_id = 1
        else:
            run_id = Extract.objects.filter(owner=user).aggregate(Max('extract_run_id'))['extract_run_id__max'] + 1
        logger.debug('handle_uploaded_file:- new run_id: %d' %(run_id))

        # Check for previous Extracts from same account and then just use those settings
        dialect = csv.Sniffer().sniff(f.read(1024))
        f.seek(0)
        has_header = csv.Sniffer().has_header(f.read(1024))
        f.seek(0)
        if Extract.objects.filter(owner=user, account=BankAccount.objects.get(owner=user, id=account_id)).exists():
            e = Extract.objects.filter(owner=user, account=BankAccount.objects.get(owner=user, id=account_id))\
                .order_by('-extract_run_id').first()
            e.pk = None
            e.extract_run_id = run_id
            e.save()
            guess_cols = False
        else:
            e = Extract.objects.create(
                account=BankAccount.objects.get(owner=user, id=account_id),
                extract_run_id=run_id,
                has_header_row=has_header,
                delimiter=dialect.delimiter,
                owner=user,
            )
            guess_cols = True
        logger.debug('handle_uploaded_file:- dialect: %s, has_header: %s, delimiter: %s' % (dialect, has_header, dialect.delimiter))

        reader = csv.reader(f, dialect)
        field_date_cols = {}
        field_incoming_cols = {}
        field_outgoing_cols = {}
        field_outgoing_cols_neg = {}
        field_description_cols = {}
        for line in f:
        # for row in reader:
            row = reader.next()
            logger.debug('handle_uploaded_file:- line %s' % (line.strip()))

            # Longest field likely to be description
            if guess_cols and (not has_header or (has_header and reader.line_num != 1)):
                inc_dict_value(field_description_cols, row.index(max(row, key=len)) + 1)    # Extract field list is 1-based
                logger.debug('handle_uploaded_file:- field_description_cols %s' % (field_description_cols))

            field_number = 1
            for field in row:
                if (guess_cols):
                    # Look for dates
                    field_date = dateparser.parse(field, languages=[get_language()[:2]])
                    if field_date is not None:
                        if field_date <= datetime.today():
                            inc_dict_value(field_date_cols, field_number)

                    # Look for incoming/outgoing
                    if has_header and reader.line_num == 1:
                        if 'Credit' in field:
                            inc_dict_value(field_incoming_cols, field_number)
                        if 'Debit' in field:
                            inc_dict_value(field_outgoing_cols, field_number)
                        logger.debug('handle_uploaded_file:- it''s a decimal: %s, incoming: %s, outgoing: %s' % (field, field_incoming_cols, field_outgoing_cols))
                    try:
                        if float(field) >= 0:
                            if re.search('\.\d\d$', field) is not None:
                                if len(field_incoming_cols.keys()) == 0:    # only match if no match found in header
                                    inc_dict_value(field_incoming_cols, field_number)
                                if len(field_incoming_cols.keys()) == 0:    # only match if no match found in header
                                    inc_dict_value(field_outgoing_cols, field_number)
                        else:
                            inc_dict_value(field_outgoing_cols, field_number)
                            inc_dict_value(field_outgoing_cols_neg, field_number)
                    except ValueError:
                        pass

                    field_number += 1

            # load into transaction object
            t = Transaction.objects.create(
                run=e,
                raw_text=line,
                row_number=reader.line_num,
                owner=user,
            )
            t.save()

        if guess_cols:
            e.fields_payment_date = dict_max_value(field_date_cols)
            e.fields_incoming = dict_max_value(field_incoming_cols)
            e.fields_outgoing = dict_max_value(field_outgoing_cols)
            e.fields_outgoing_sign = '-' if dict_max_value(field_outgoing_cols_neg) == e.fields_outgoing else '+'
            e.fields_description = dict_max_value(field_description_cols)
            e.save()

        return run_id

    except Exception as e:
        error_message = '{ "Exception": "%s" }' % \
                        (e.messages if hasattr(e, 'messages') else e.message)
        logger.error(error_message)
        return -1

# endregion

# region Helper functions


def dict_max_value(d):
    k = list(d.keys())
    v = list(d.values())
    return -1 if len(v) == 0 else k[v.index(max(v))]


def inc_dict_value(d, k):
    d[k] = 1 if k not in d else d[k] + 1

# endregion