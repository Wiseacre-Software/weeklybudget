# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-10 03:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0016_auto_20170609_0555'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='account_type',
            field=models.CharField(default=b'debit', max_length=20),
        ),
        migrations.AddField(
            model_name='historicalbankaccount',
            name='account_type',
            field=models.CharField(default=b'debit', max_length=20),
        ),
    ]
