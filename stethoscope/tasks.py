from celery.task import Task
from celery.registry import tasks
from celery.utils.log import get_task_logger

from urlparse import urlparse

import requests
import logging
import datetime
import pytz

from django.conf import settings

from django.core.cache import cache
from django.contrib.auth.models import User

from django.db.models import Q
from ssd.dashboard.models import Event, Event_Update, Service, Config_Message, Type, Status, Event_Service
from stethoscope.models import Service_Monitor


logger = get_task_logger(__name__)

class Listen_For_Heartbeat(Task):
    ignore_result = True
    def run(self, **kwargs):
        logger.debug("Started Listen_For_Heartbeat Task")

        service_monitors = Service_Monitor.objects.all()
        sm_list = []
        for s in service_monitors:
            sm_list.append(s.name) # To check later if we monitor a service which has an open issue with 'in' operator.

        for s in service_monitors:
            """ Iterate through all services to be monitored. """
            url_o = urlparse(s.url)
            # Fetch open incidents at each iteration. To stay consistent.
            open_incidents = Event.objects.filter(Q(status__status='open') & Q(type__type='incident')).values('id','description').order_by('start')
            logger.debug("Probing %s (id: %s)" % (s.name, s.id))
            if s.test_type == 'HTTP':
                error_desc = None
                try:
                    r = requests.get(s.url, verify=True, timeout=5)
                except requests.exceptions.SSLError as e:
                    error_desc = 'Unable to validate SSL certificate.'
                except requests.exceptions.Timeout as e:
                    error_desc = 'Service timed out when trying to access it over %s. Website must load in 5 seconds for optimal user experience.' % (url_o.scheme)
                except requests.exceptions.ConnectionError as e:
                    error_desc = 'Unable to establish a %s connection with the service.' % (url_o.scheme)

                if r.status_code / 100 != 2:
                    error_desc = 'Website not returning %s 2xx Success status code. Got %s' % (url_o.scheme, r.status_code)

                logger.debug("%s (id: %s) Status: %s, Error: %s" % (s.name, s.id, r.status_code, error_desc))
                open_issue = None
                for incident in open_incidents:
                    dash_location = incident['description'].find(' [%s] -- ' % (url_o.scheme))
                    if dash_location is None:
                        continue
                    i_service_name = incident['description'][:dash_location]
                    if i_service_name in sm_list and i_service_name == s.name:
                        # We monitor this issue and the issue was probably raised by us
                        open_issue = incident['id']

                if error_desc is None and open_issue is not None:
                    # Website returned to normal state. Close the issue.
                    logger.debug("Closing issue in site %s id: %s..." % (s.name, s.id))
                    time_now = datetime.datetime.now()
                    time_now = pytz.timezone(settings.TIME_ZONE).localize(time_now)
                    try:
                        user = User.objects.get(username='netadmin')
                    except DoesNotExist:
                        user = User.objects.order_by(pk)[0]
                    Event.objects.filter(id=open_issue).update(
                            status=Status.objects.filter(status='closed').values('id')[0]['id'],
                            end=time_now
                    )
                    Event_Update(
                            event_id=open_issue, 
                            date=time_now, 
                            update='%s service to %s resumed normal operation.' % (url_o.scheme, s.name), 
                            user_id=user.id
                    ).save()
                    cache.delete_many(['timeline','events_ns','event_count_ns'])
                    logger.debug("Issue closed in site %s id: %s..." % (s.name, s.id))
                elif error_desc is not None and open_issue is not None:
                    # Website state not normal and an issue exists.
                    # Ignore for now.
                    # [TODO] Can update the issue if new problem arises in the future.
                    logger.debug("Site %s id: %s. Pending issue ID: %s" % (s.name, s.id, open_issue))
                    logger.debug("Current issue: %s" % (error_desc))
                    continue
                elif error_desc is None and open_issue is None:
                    # Website state normal and no issue present.
                    logger.debug("Website %s (id: %s) operating normally." % (s.name, s.id))
                    continue
                else:
                    # No open issue. Website state not normal. Create new issue
                    logger.debug("Creating issue for site %s id %s..." % (s.name, s.id))
                    time_now = datetime.datetime.now()
                    time_now = pytz.timezone(settings.TIME_ZONE).localize(time_now)
                    try:
                        user = User.objects.get(username='netadmin')
                    except DoesNotExist:
                        user = User.objects.order_by(pk)[0]
                    e = Event.objects.create(
                            type_id=Type.objects.filter(type='incident').values('id')[0]['id'],
                            description='%s [%s] -- %s' % (s.name, url_o.scheme, error_desc),
                            status_id=Status.objects.filter(status='open').values('id')[0]['id'],
                            start=time_now,
                            end=None,
                            user_id = user.id
                    )
                    event_id = e.pk

                    # Find out which services this impacts and associate the services with the event
                    for affected_service in s.affected_services.all():
                        Event_Service(service_id=affected_service.id,event_id=event_id).save()
                    cache.delete_many(['timeline','events_ns','event_count_ns'])
                    logger.debug("Created issue for site %s id %s..." % (s.name, s.id))
                    logger.debug("Issue is: %s" % (error_desc))
        logger.debug("Finished Listen_For_Heartbeat Task")

tasks.register(Listen_For_Heartbeat)
