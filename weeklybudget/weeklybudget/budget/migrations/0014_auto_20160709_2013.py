# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-09 10:13
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0013_auto_20160709_2008'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='HistoricalPaymentScheduleExclusions',
            new_name='HistoricalPaymentScheduleExclusion',
        ),
        migrations.RenameModel(
            old_name='PaymentScheduleExclusions',
            new_name='PaymentScheduleExclusion',
        ),
        migrations.AlterModelOptions(
            name='historicalpaymentscheduleexclusion',
            options={'get_latest_by': 'history_date', 'ordering': ('-history_date', '-history_id'), 'verbose_name': 'historical payment schedule exclusion'},
        ),
    ]
