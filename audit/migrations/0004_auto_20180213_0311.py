# -*- coding: utf-8 -*-
# Generated by Django 1.10.4 on 2018-02-13 03:11
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0003_auto_20180212_1426'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='val',
            field=models.CharField(max_length=128, unique=True, verbose_name='Token'),
        ),
        migrations.AlterUniqueTogether(
            name='token',
            unique_together=set([]),
        ),
    ]
