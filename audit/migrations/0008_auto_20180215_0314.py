# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-02-15 03:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0007_auto_20180215_0311'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tasklog',
            name='result',
            field=models.TextField(default='init...', verbose_name='命令结果'),
        ),
    ]
