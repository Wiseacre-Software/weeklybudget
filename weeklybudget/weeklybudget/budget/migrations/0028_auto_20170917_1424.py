# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-17 04:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0027_auto_20170917_0905'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='account_limit',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=18, null=True),
        ),
        migrations.AlterField(
            model_name='historicalbankaccount',
            name='account_limit',
            field=models.DecimalField(decimal_places=4, default=0, max_digits=18, null=True),
        ),
    ]