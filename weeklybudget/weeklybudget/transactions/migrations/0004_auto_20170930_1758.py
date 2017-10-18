# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-30 07:58
from __future__ import unicode_literals

import datetime
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0003_auto_20170930_1604'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaltransaction',
            name='extract_date',
            field=models.DateTimeField(blank=True, default=datetime.datetime(2017, 9, 30, 0, 0), editable=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicaltransaction',
            name='extract_run_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transaction',
            name='extract_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transaction',
            name='extract_run_id',
            field=models.IntegerField(default=0),
            preserve_default=False,
        ),
    ]