"""
BaseWidget is the a base class that can be extended to make marimo widget handlers 
"""
import json

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse

MARIMO_TIMEOUT = getattr(settings, 'MARIMO_TIMEOUT', 60*60*24)

class BaseWidget(object):
    """
    Extend BaseWidget to make marimo widget handlers.
    template: the template that this widget will use
    use_cache:  If nothing is cacheable in your handler set this to false and don't define a cacheable method
    cacheable:  This should accept a dictionary argument *args and **kwargs.  
                Everything in this part will be cached using your cache_key method
    uncacheable: This takes a dictionary and will modify it with uncacheable information
    cache_key:  This is they key 

    """
    # TODO: make this a view by wrapping the __call__
    # TODO: everything seems stateless should these be classmethods?

    use_cache = True

    def cacheable(self, response, *args, **kwargs):
        """
        Should be overriden in subclasses if use_cache=True
        should update response with cacheable information and return it
        """
        return response

    def uncacheable(self, request, response, *args, **kwargs):
        """
        should update context based on request specific information and return it
        """
        return response

    def cache_key(self, *args, **kwargs):
        """
        Must be overridden in subclass if use_cache=True
        Generates the cache key that this widget will use based on  *args and **kwargs
        """
        raise NotImplementedError

    def get_cache(self, *args, **kwargs):
        """ get current cached cacheable part """
        cache_key = self.cache_key(*args, **kwargs)
        response = cache.get(cache_key)
        if response is None:
            response = {'template':self.template, 'context':dict()}
            response = self.update_cache(response, *args, **kwargs)
        return response

    def update_cache(self, response, *args, **kwargs):
        """ call this with *args and **kwargs like a request to update the cache """
        cache_key = self.cache_key(*args, **kwargs)
        response = self.cacheable(response, *args, **kwargs)
        cache.set(cache_key, response, MARIMO_TIMEOUT)
        return response

    def on_error(self, ex, data, request, *args, **kwargs):
        """ override this to provide custom exception handling """
        # TODO fix tracebacks
        if getattr(settings, 'DEBUG', False):
            raise ex
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
