from django.contrib import admin

from .models import Service_Monitor

class Service_MonitorAdmin(admin.ModelAdmin):
	pass
admin.site.register(Service_Monitor, Service_MonitorAdmin)
