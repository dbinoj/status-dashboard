# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stethoscope', '0005_auto_20151026_2123'),
    ]

    operations = [
        migrations.RenameField(
            model_name='service_monitor',
            old_name='services',
            new_name='affected_services',
        ),
    ]
