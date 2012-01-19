"""
BaseWidget is the a base class that can be extended to make marimo widget handlers
"""
import json
import sys
import traceback

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

MARIMO_TIMEOUT = getattr(settings, 'MARIMO_TIMEOUT', 60*60*24)

class BaseWidget(object):
    """
    Extend BaseWidget to make marimo widget handlers.

    Properties::

        use_cache:  If nothing is cacheable in your handler set this to false and don't define a cacheable method
        template:   A string; the template data that this widget will use. (Not a filename.)

    To load a template from a file, consider:

        template = template_loader.load('my_template.html')

    ... which will look for its path relative to a dir in MARIMO_TEMPLATE_DIRS.

    """
    use_cache = True
    template = ''

    # TODO: everything seems stateless should these be classmethods?
    def cacheable(self, response, *args, **kwargs):
        """
        Updates and returns response dictionary with cacheable data.

        Should be overriden in subclasses if use_cache=True
        """
        return response

    def uncacheable(self, request, response, *args, **kwargs):
        """
        Updates response dictionary with uncacheable data.

        Should be overwritten in all subclasses.
        """
        return response

    def cache_key(self, *args, **kwargs):
        """
        Generates the cache key that this widget will use based on  *args and **kwargs

        Must be overridden in subclass if use_cache=True
        """
        raise NotImplementedError

    def get_cache(self, *args, **kwargs):
        """ get current cached cacheable part """
        cache_key = self.cache_key(*args, **kwargs)
        response = cache.get(cache_key)
        if response is None:
            response = self.update_cache(response, *args, **kwargs)
        return response

    def update_cache(self, response, *args, **kwargs):
        """ call this with *args and **kwargs like a request to update the cache """
        cache_key = self.cache_key(*args, **kwargs)
        if response is None:
            response = {'template':self.template, 'context':dict()}
        response = self.cacheable(response, *args, **kwargs)
        cache.set(cache_key, response, MARIMO_TIMEOUT)
        return response

    def on_error(self, ex, data, request, *args, **kwargs):
        """ override this to provide custom exception handling """
        if getattr(settings, 'DEBUG', False):
            exc_type, exc_value, exc_traceback = sys.exc_info()
            data['error'] = {
                'type':repr(exc_type),
                'value':repr(exc_value),
                'traceback':'\n'.join(traceback.format_exception(exc_type,exc_value,exc_traceback)),
            }
        else:
            data['msg'] = 'exception hidden. set DEBUG to true to get more info'
        data['status'] = 'failed'
        return data

    def __call__(self, request, *args, **kwargs):
        """
        Splits up work into cachable and uncacheable parts
        """

        if self.use_cache:
            response = self.get_cache(*args, **kwargs)
        else:
            response = {'template':self.template, 'context':dict()}

        response = self.uncacheable(request, response, *args, **kwargs)
        return response

    @classmethod
    def as_view(cls):
        """ as_view can be used to create views for marimo widgets only reccomended for debugging """
        def view(request):
            inst = cls()
            data = json.loads(request.GET['data'])
            response = inst(request, *data['args'], **data['kwargs'])
            return HttpResponse(json.dumps(response), mimetype='application/json')
        return view
