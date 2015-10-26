# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '__first__'),
        ('stethoscope', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='website',
            name='service',
            field=models.ForeignKey(default=None, to='dashboard.Service'),
            preserve_default=False,
        ),
    ]
