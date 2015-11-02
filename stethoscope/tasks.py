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
from django.utils import timezone

from django.db.models import Q
from ssd.dashboard.models import Event, Event_Update, Service, Config_Message, Type, Status, Event_Service
from stethoscope.models import Service_Monitor

from stethoscope import inspector

logger = get_task_logger(__name__)

class Listen_For_Heartbeat(Task):
    ignore_result = True
    def run(self, **kwargs):
        service_monitors = Service_Monitor.objects.all()
        for sm in service_monitors:
            """ Iterate through all services to be monitored. """

            try:
                service_inspector = getattr(inspector, sm.test_type)
            except AttributeError:
                raise Exception('Service Inspector for %s not implemented.')
                continue
            else:
                service = service_inspector(sm.url)

            url_o = service.get_url_object()

            today = timezone.now().date()
            tomorrow = today + datetime.timedelta(1)
            today_start = datetime.datetime.combine(today, datetime.time())
            today_start = pytz.timezone(settings.TIME_ZONE).localize(today_start)
            today_end = datetime.datetime.combine(tomorrow, datetime.time())
            today_end = pytz.timezone(settings.TIME_ZONE).localize(today_end)
            time_now = datetime.datetime.now()
            time_now = pytz.timezone(settings.TIME_ZONE).localize(time_now)

            # Fetch open incidents for current service created by us at each iteration. To stay consistent.
            # We select the issues based on the pattern in which we crete the description.
            open_incidents = Event.objects.filter(
                    Q(status__status='open') & 
                    Q(type__type='incident') & 
                    Q(description__startswith='%s [%s] -- ' % (sm.name, url_o.scheme))
            ).order_by('-start').values('id','description')
            
            # Fetch incidents for the service affected which were closed today.
            incidents_started_today_closed = Event.objects.filter(
                    Q(status__status='closed') & 
                    Q(type__type='incident') & 
                    Q(start__lte=today_end) & 
                    Q(start__gte=today_start) & 
                    Q(description__startswith='%s [%s] -- ' % (sm.name, url_o.scheme))
            ).order_by('-end').values('id','description')

            # User under whose name updates should be made.
            try:
                user = User.objects.get(username='netadmin')
            except DoesNotExist:
                user = User.objects.order_by(pk)[0]

            open_issue = None
            closed_issue = None

            if open_incidents:
                open_issue = open_incidents[0]['id']

            if incidents_started_today_closed:
                closed_issue = incidents_started_today_closed[0]['id']

            """ Decision matrix on how to proceed.
            We want only one active issue for a service monitor.

            OUTCOME                     | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
            SERVICE_UP                  | Y | Y | Y | Y | N | N | N | N |
            HAS_OPEN_ISSUES             | N | Y | N | Y | N | Y | N | Y |
            HAS_ISSUES_WERE_CLOSED_TODAY| N | N | Y | Y | N | N | Y | Y |
            DECISIONS:
            1. Do nothin and skip current iteration (continue)
            2. Close all open issues and skip current iteration
            3. Do nothin and skip current iteration
            4. Close all open issues and skip current iteration
            5. Open new issue and skip current iteration
            6. Close all but latest issue (if multiple issues open) and skip current iteration
            7. Reopen last closed issue, update error message and skip current iteration
            8. Close all but latest issue (if multiple issues open), update last open issue with error message and skip current iteration
            """
            if service.is_up() and open_issue is None and closed_issue is None:
                # Case 1
                continue
            if service.is_up() and open_issue is not None and closed_issue is None:
                # Case 2
                for incident in open_incidents:
                    Event.objects.filter(id=incident['id']).update(
                            status=Status.objects.filter(status='closed').values('id')[0]['id'],
                            end=time_now
                    )
                    Event_Update(
                            event_id=incident['id'], 
                            date=time_now, 
                            update='%s service to %s resumed normal operation.' % (url_o.scheme, sm.name), 
                            user_id=user.id
                    ).save()
                    cache.delete_many(['timeline','events_ns','event_count_ns'])
                continue
            if service.is_up() and open_issue is None and closed_issue is not None:
                # Case 3
                continue
            if service.is_up() and open_issue is not None and closed_issue is not None:
                # Case 4
                for incident in open_incidents:
                    Event.objects.filter(id=incident['id']).update(
                            status=Status.objects.filter(status='closed').values('id')[0]['id'],
                            end=time_now
                    )
                    Event_Update(
                            event_id=incident['id'], 
                            date=time_now, 
                            update='%s service to %s resumed normal operation.' % (url_o.scheme, sm.name), 
                            user_id=user.id
                    ).save()
                    cache.delete_many(['timeline','events_ns','event_count_ns'])
                continue
            if not service.is_up() and open_issue is None and closed_issue is None:
                # Case 5
                e = Event.objects.create(
                        type_id=Type.objects.filter(type='incident').values('id')[0]['id'],
                        description='%s [%s] -- %s' % (sm.name, url_o.scheme, service.error_msg()),
                        status_id=Status.objects.filter(status='open').values('id')[0]['id'],
                        start=time_now,
                        end=None,
                        user_id = user.id
                )
                event_id = e.pk

                # Find out which services this impacts and associate the services with the event
                for affected_service in sm.affected_services.all():
                    Event_Service(service_id=affected_service.id,event_id=event_id).save()

                cache.delete_many(['timeline','events_ns','event_count_ns'])
                continue
            if not service.is_up() and open_issue is not None and closed_issue is None:
                # Case 6
                if len(open_incidents) > 1:
                    for index, incident in enumerate(open_incidents):
                        if index == 0:
                            continue
                        Event.objects.filter(id=incident['id']).update(
                                status=Status.objects.filter(status='closed').values('id')[0]['id'],
                                end=time_now
                        )
                        Event_Update(
                                event_id=incident['id'], 
                                date=time_now, 
                                update='Closing duplicate incident.', 
                                user_id=user.id
                        ).save()
                        cache.delete_many(['timeline','events_ns','event_count_ns'])
                continue
            if not service.is_up() and open_issue is None and closed_issue is not None:
                # Case 7
                Event.objects.filter(id=closed_issue).update(
                        status=Status.objects.filter(status='open').values('id')[0]['id'],
                        end=None
                )
                Event_Update(
                        event_id=closed_issue, 
                        date=time_now, 
                        update='%s [%s] -- %s' % (sm.name, url_o.scheme, service.error_msg()),
                        user_id=user.id
                ).save()
                cache.delete_many(['timeline','events_ns','event_count_ns'])
                continue
            if not service.is_up() and open_issue is not None and closed_issue is not None:
                # Case 8
                if len(open_incidents) > 1:
                    for index, incident in enumerate(open_incidents):
                        if index == 0:
                            continue
                        Event.objects.filter(id=incident['id']).update(
                                status=Status.objects.filter(status='closed').values('id')[0]['id'],
                                end=time_now
                        )
                        Event_Update(
                                event_id=incident['id'], 
                                date=time_now, 
                                update='Closing duplicate incident.', 
                                user_id=user.id
                        ).save()
                        cache.delete_many(['timeline','events_ns','event_count_ns'])
                Event_Update(
                        event_id=open_issue, 
                        date=time_now, 
                        update='%s [%s] -- %s' % (sm.name, url_o.scheme, service.error_msg()),
                        user_id=user.id
                ).save()
                continue
tasks.register(Listen_For_Heartbeat)
