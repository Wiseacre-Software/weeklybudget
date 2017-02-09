# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-06-12 23:34
from __future__ import unicode_literals

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0007_bankaccount'),
    ]

    operations = [
        migrations.AddField(
            model_name='payment',
            name='eff_date',
            field=models.DateTimeField(default=datetime.datetime(2016, 6, 13, 9, 34, 53, 390000), verbose_name=b'effective date'),
        ),
        migrations.AddField(
            model_name='payment',
            name='exp_date',
            field=models.DateTimeField(default=datetime.datetime(9999, 12, 31, 23, 59, 59, 999999), verbose_name=b'expiry date'),
        ),
    ]
