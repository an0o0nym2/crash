# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-07-19 14:24
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('processor', '0006_bugreport_fixed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='processedcrash',
            name='crash_cause',
            field=models.CharField(default='SIGSEGV', max_length=100),
        ),
    ]