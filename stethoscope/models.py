from django.db import models
from ssd.dashboard.models import Service

class Service_Monitor(models.Model):
    TEST_TYPES = (
        ('HTTP', 'HTTP/HTTPS'),
        ('SSH', 'SSH'),
        ('RTMP', 'RTMP'),
        ('ICMP', 'PING/ICMP'),
    )
    name = models.CharField(max_length=300)
    url = models.URLField(max_length=2000)
    affected_services =  models.ManyToManyField(Service)
    test_type = models.CharField(max_length=10, choices=TEST_TYPES, help_text="Only HTTP/HTTPS implemented ATM.")

    def __str__(self):
        return self.name
