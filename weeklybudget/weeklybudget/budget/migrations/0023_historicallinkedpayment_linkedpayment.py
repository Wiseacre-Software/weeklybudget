# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-23 08:09
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('budget', '0022_auto_20170709_1051'),
    ]

    operations = [
        migrations.CreateModel(
            name='HistoricalLinkedPayment',
            fields=[
                ('id', models.IntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('offset', models.SmallIntegerField(default=0)),
                ('offset_type', models.CharField(max_length=40)),
                ('end_date', models.DateField(blank=True, null=True, verbose_name=b'Last Payment Date')),
                ('occurrences', models.SmallIntegerField(default=0)),
                ('active', models.BooleanField(default=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField()),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('linked_payment', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='budget.Payment')),
                ('main_payment', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='budget.Payment')),
                ('owner', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': 'history_date',
                'verbose_name': 'historical linked payment',
            },
        ),
        migrations.CreateModel(
            name='LinkedPayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('offset', models.SmallIntegerField(default=0)),
                ('offset_type', models.CharField(max_length=40)),
                ('end_date', models.DateField(blank=True, null=True, verbose_name=b'Last Payment Date')),
                ('occurrences', models.SmallIntegerField(default=0)),
                ('active', models.BooleanField(default=True)),
                ('linked_payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='budget.Payment')),
                ('main_payment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='linked_to', to='budget.Payment')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
