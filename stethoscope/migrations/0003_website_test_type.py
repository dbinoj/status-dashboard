# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('stethoscope', '0002_website_service'),
    ]

    operations = [
        migrations.AddField(
            model_name='website',
            name='test_type',
            field=models.CharField(default='HTTP', max_length=10, choices=[(b'HTTP', b'HTTP/HTTPS'), (b'SSH', b'SSH'), (b'RTMP', b'RTMP'), (b'ICMP', b'PING/ICMP')]),
            preserve_default=False,
        ),
    ]
