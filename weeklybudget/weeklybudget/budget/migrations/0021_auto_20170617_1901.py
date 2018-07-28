# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-17 09:01
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0020_auto_20170614_0925'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='account_limit',
            field=models.DecimalField(decimal_places=4, max_digits=18, null=True),
        ),
        migrations.AddField(
            model_name='historicalbankaccount',
            name='account_limit',
            field=models.DecimalField(decimal_places=4, max_digits=18, null=True),
        ),
    ]
