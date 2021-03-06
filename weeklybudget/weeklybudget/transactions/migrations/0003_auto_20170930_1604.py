# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-09-30 06:04
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transactions', '0002_auto_20170930_1505'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaltransaction',
            name='raw_text',
            field=models.CharField(default='', max_length=800),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='historicaltransaction',
            name='status',
            field=models.CharField(default='new', max_length=20),
        ),
        migrations.AddField(
            model_name='transaction',
            name='raw_text',
            field=models.CharField(default='', max_length=800),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='transaction',
            name='status',
            field=models.CharField(default='new', max_length=20),
        ),
        migrations.AlterField(
            model_name='historicaltransaction',
            name='amount',
            field=models.DecimalField(decimal_places=4, max_digits=18, null=True),
        ),
        migrations.AlterField(
            model_name='historicaltransaction',
            name='description',
            field=models.CharField(blank=True, max_length=800),
        ),
        migrations.AlterField(
            model_name='historicaltransaction',
            name='in_out',
            field=models.CharField(blank=True, default='o', max_length=1),
        ),
        migrations.AlterField(
            model_name='historicaltransaction',
            name='payment_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='amount',
            field=models.DecimalField(decimal_places=4, max_digits=18, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='description',
            field=models.CharField(blank=True, max_length=800),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='in_out',
            field=models.CharField(blank=True, default='o', max_length=1),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='payment_date',
            field=models.DateTimeField(null=True),
        ),
    ]
