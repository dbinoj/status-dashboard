import os
import datetime

from urlparse import urlparse


class ServiceInspector(object):
    url = None
    url_o = None

    _service_up = None
    _error_msg = None

    def __init__(self, url=None):
        self.set_url(url)
        self.gen_urlobject()
        self.check()
    
    def set_url(self, url):
        if url is None:
            raise Exception('URL should be passed while initializing an inspector.')
        self.url = url

    def set_error_msg(self, error_msg):
        self._error_msg = error_msg

    def gen_urlobject(self):
        self.url_o = urlparse(self.url)
    
    def error_msg(self):
        return self._error_msg

    def is_up(self):
        return self._service_up

    def status(self):
        if self._service_up:
            return 'UP'
        else:
            return 'DOWN'

    def get_url_object(self):
        return self.url_o

    def check(self):
        """ Checks if the service is functioning normally. """
        if self._service_up is None:
            result = self.inspect()
            self.set_error_msg(result)
        if self._error_msg is None:
            self._service_up = True
        else:
            self._service_up = False

    def inspect(self):
        """The real checking process for the service. Redefine in subclasses."""
        pass

    @property
    def SI_NAME(self):
        return type(self).__name__[:-2]
