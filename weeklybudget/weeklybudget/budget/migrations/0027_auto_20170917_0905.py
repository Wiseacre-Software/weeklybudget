# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-16 23:05
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0026_auto_20170916_1834'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='display_order',
            field=models.SmallIntegerField(default=0),
        ),
        migrations.AddField(
            model_name='historicalbankaccount',
            name='display_order',
            field=models.SmallIntegerField(default=0),
        ),
    ]
