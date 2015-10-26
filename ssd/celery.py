from __future__ import absolute_import

import os

from celery import Celery
from datetime import timedelta

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ssd.settings')

from django.conf import settings

app = Celery('ssd')

# Using a string here means the worker will not have to
# pickle the object when using Windows.
app.config_from_object('django.conf:settings')

app.conf.update(
    CELERYBEAT_SCHEDULE = {
        'check-services-for-heartbeat': {
            'task': 'stethoscope.tasks.Listen_For_Heartbeat',
            'schedule': timedelta(seconds=60),
        },
    }
)
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
