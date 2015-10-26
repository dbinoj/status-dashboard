# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stethoscope', '0004_auto_20151026_1945'),
    ]

    operations = [
        migrations.RenameField(
            model_name='service_monitor',
            old_name='service',
            new_name='services',
        ),
    ]
