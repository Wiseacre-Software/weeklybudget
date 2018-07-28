# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=200)),
                ('amount', models.DecimalField(max_digits=18, decimal_places=4)),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name=b'create date')),
            ],
        ),
        migrations.CreateModel(
            name='PaymentSchedule',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('next_date', models.DateField(null=True, verbose_name=b'Next Payment Date')),
                ('end_date', models.DateField(null=True, verbose_name=b'Last Payment Date')),
                ('occurrences', models.SmallIntegerField(default=1)),
                ('weekly_dow_mon', models.BooleanField()),
                ('weekly_dow_tue', models.BooleanField()),
                ('weekly_dow_wed', models.BooleanField()),
                ('weekly_dow_thu', models.BooleanField()),
                ('weekly_dow_fri', models.BooleanField()),
                ('weekly_dow_sat', models.BooleanField()),
                ('weekly_dow_sun', models.BooleanField()),
                ('weekly_frequency', models.SmallIntegerField(default=1)),
                ('monthly_dom', models.SmallIntegerField(default=1)),
                ('monthly_frequency', models.SmallIntegerField(default=1)),
                ('monthly_wom', models.SmallIntegerField(default=0)),
                ('monthly_dow', models.SmallIntegerField(default=0)),
                ('annual_dom', models.SmallIntegerField(default=1)),
                ('annual_moy', models.SmallIntegerField(default=1)),
                ('annual_frequency', models.SmallIntegerField(default=1)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentScheduleFrequency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('sort_order', models.SmallIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentType',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('sort_order', models.SmallIntegerField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='SubCategory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=200)),
                ('category', models.ForeignKey(to='budget.Category')),
            ],
        ),
        migrations.AddField(
            model_name='paymentschedule',
            name='frequency',
            field=models.ForeignKey(to='budget.PaymentScheduleFrequency'),
        ),
        migrations.AddField(
            model_name='payment',
            name='schedule',
            field=models.ForeignKey(to='budget.PaymentSchedule', null=True),
        ),
        migrations.AddField(
            model_name='payment',
            name='subcategory',
            field=models.ForeignKey(to='budget.SubCategory', null=True),
        ),
        migrations.AddField(
            model_name='category',
            name='payment_type',
            field=models.ForeignKey(default=0, to='budget.PaymentType'),
        ),
    ]
