import requests
import datetime
import pytz

from django.core.cache import cache
from django.contrib.auth.models import User
from django.db.models import Q

from ssd.dashboard.models import (
        Event, 
        Event_Update, 
        Service, 
        Config_Message, 
        Type, 
        Status, 
        Event_Service
)
from stethoscope.models import Service_Monitor

from .inspector import ServiceInspector

class HTTP(ServiceInspector):
    SI_NAME = 'HTTP'

    def inspect(self):
        error_desc = None
        try:
            r = requests.get(self.url, verify=True, timeout=5)
            if r.status_code / 100 != 2:
                error_desc = 'Website not returning %s 2xx Success status code. Got %s' % (self.url_o.scheme, r.status_code)
        except requests.exceptions.SSLError as e:
            error_desc = 'Unable to validate SSL certificate.'
        except requests.exceptions.Timeout as e:
            error_desc = 'Service timed out when trying to access it over %s. Website must load in 5 seconds for optimal user experience.' % (self.url_o.scheme)
        except requests.exceptions.ConnectionError as e:
            error_desc = 'Unable to establish a %s connection with the service.' % (self.url_o.scheme)

        return error_desc
