# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models
from simple_history.models import HistoricalRecords

from budget.models import *


class Extract(models.Model):
    account = models.ForeignKey(BankAccount, null=True, blank=True)
    status = models.CharField(max_length=20, default='new') # 'new': line read into raw_text field
    extract_date = models.DateTimeField(auto_now_add=True)
    extract_run_id = models.IntegerField()
    has_header_row = models.BooleanField(default=False)
    delimiter = models.CharField(max_length=20, default=',')
    fields_payment_date = models.IntegerField(default=-1) # column number (0 based) of date field in extract
    fields_description = models.IntegerField(default=-1)  # column number (0 based) of description field in extract
    fields_incoming = models.IntegerField(default=-1)  # column number (0 based) of incoming amount field in extract
    fields_incoming_sign = models.CharField(max_length=1, default='+')  # incoming amount field is positive or negative
    fields_outgoing = models.IntegerField(default=-1)  # column number (0 based) of outgoing amount field in extract
    fields_outgoing_sign = models.CharField(max_length=1, default='+')  # outgoing amount field is positive or negative

    owner = models.ForeignKey(User)
    history = HistoricalRecords()


class Transaction(models.Model):
    run = models.ForeignKey(Extract, null=True)
    raw_text = models.CharField(max_length=800)
    row_number = models.IntegerField()
    payment_date = models.DateTimeField(null=True)
    description = models.CharField(max_length=800, blank=True)
    payment = models.ForeignKey(Payment, null=True, blank=True)
    in_out = models.CharField(max_length=1, default='o', blank=True)  # i: incoming; o: outgoing
    amount = models.DecimalField(max_digits=18, decimal_places=4, null=True)
    payment_type = models.ForeignKey(PaymentType, null=True, blank=True)
    category = models.ForeignKey(Category, null=True, blank=True)
    subcategory = models.ForeignKey(SubCategory, null=True, blank=True)
    account = models.ForeignKey(BankAccount, null=True, blank=True)
    status = models.CharField(max_length=20, default='new') # 'new': line read into raw_text field

    owner = models.ForeignKey(User)
    history = HistoricalRecords()


