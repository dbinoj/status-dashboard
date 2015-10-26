# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dashboard', '__first__'),
        ('stethoscope', '0003_website_test_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='Service_Monitor',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300)),
                ('url', models.URLField(max_length=2000)),
                ('test_type', models.CharField(help_text=b'Only HTTP/HTTPS implemented ATM.', max_length=10, choices=[(b'HTTP', b'HTTP/HTTPS'), (b'SSH', b'SSH'), (b'RTMP', b'RTMP'), (b'ICMP', b'PING/ICMP')])),
                ('service', models.ManyToManyField(to='dashboard.Service')),
            ],
        ),
        migrations.RemoveField(
            model_name='website',
            name='service',
        ),
        migrations.DeleteModel(
            name='Website',
        ),
    ]
