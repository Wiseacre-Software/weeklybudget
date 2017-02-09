# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-07-09 10:22
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0014_auto_20160709_2013'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalpaymentscheduleexclusion',
            name='exclusion_date',
            field=models.DateField(default=datetime.datetime(2016, 7, 9, 10, 22, 5, 237000, tzinfo=utc)),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='paymentscheduleexclusion',
            name='exclusion_date',
            field=models.DateField(default='2016-12-01'),
            preserve_default=False,
        ),
    ]