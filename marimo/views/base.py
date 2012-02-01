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

class BaseWidgetHandler(object):
    """
    Extend BaseWidget to make marimo widget handlers.

    If part of the data in your handler is cacheable, override cacheable() and
    cache_key(). If no data in your handler is cacheable, don't override
    cache_key().

    """

    def default_response(self, *args, **kwargs):
        """A default response to pass into cacheable(), which will be modified
        and eventually returned.

        We do this in a function because subclasses that override cacheable do
        not expect to have to call super() to get the response set by the
        parent. Subclasses that override this should call super() if they want
        the parent functionality.

        """
        return {'context': dict()}

    # TODO: everything seems stateless should these be classmethods?
    def cacheable(self, response, *args, **kwargs):
        """
        Returns a response dictionary with cacheable data.

        Should be overriden in subclasses that have cacheable data.

        Subclasses that override this method should also override cache_key.

        Subclasses should always return the updated dict; callers should use
        the return value. Do not rely on the dict passed in as 'response' to be
        modified in-place.

        Subclasses normally need not call this function, however callers should
        not assume that the dict passed in as 'response' will not be modified
        as a side-effect.

        """
        return response

    def uncacheable(self, request, response, *args, **kwargs):
        """
        Returns a response dictionary with uncacheable data.

        Should be overwritten in all subclasses.

        Subclasses should always return the updated dict; callers should use
        the return value. Do not rely on the dict passed in as 'response' to be
        modified in-place. Neither should one assume that the dict passed in as
        'response' will not be modified as a side-effect.

        """
        return response

    def cache_key(self, *args, **kwargs):
        """
        Generates the cache key that this widget will use based on  *args and **kwargs

        Must be overridden in subclasses if cacheable is overridden.

        A return value of 'None' is special; it means "do not cache for these
        args/kwargs". Don't return a cache key if you don't need to cache
        anything; otherwise the default return value of cacheable() will be
        redundantly and wastefully cached.
        """
        pass

    def get_cache(self, *args, **kwargs):
        """
        get current cached cacheable part. Updates data in cache with data from
        self.uncacheable.

        use kwarg '__force_update' to force the cache to be regenerated.
        """
        response = None
        cache_key = self.cache_key(*args, **kwargs)
        if cache_key and not kwargs.get('__force_update', False):
            response = cache.get(cache_key)
        if response is None:
            response = self.default_response(*args, **kwargs)
            response = self.cacheable(response, *args, **kwargs)
            if cache_key:
                cache.set(cache_key, response, MARIMO_TIMEOUT)
        return response

    def update_cache(self, *args, **kwargs):
        """ convenience wrapper around get_cache for cache invalidation """
        # we expect the caller to discard the return value but why not return
        # it anyway.
        return self.get_cache(__force_update=True, *args, **kwargs)

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
        """ Splits up work into cachable and uncacheable parts """
        response = self.get_cache(*args, **kwargs)
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

class RequestWidgetHandler(BaseWidgetHandler):
    """Handler (abstract superclass) for (subclasses of) marimo.widgetlib.request_widget

    To handle requests for your subclass of marimo.widgetlib.request_widget,
    create a subclass of this, overriding at minimum:

        template
        uncacheable()

    If some data is cacheable, override cache_key() and cacheable().

    This handler assumes that all requests for your widget use the same template.

    Properties::

        template:   A string; the template data that this widget will use. (Not a filename.)

    To load a template from a file relative to a dir in MARIMO_TEMPLATE_DIRS:

        template = template_loader.load('my_template.html')

    """
    template = ''

    def default_response(self, *args, **kwargs):
        """A default response to pass into cacheable(), which will be modified
        and eventually returned.

        We do this in a function because subclasses that override cacheable do
        not expect to have to call super(). Subclasses that override this
        should call super() if they want the parent functionality.

        """
        response = super(RequestWidgetHandler, self).default_response(*args, **kwargs)
        response['template'] = self.template
        return response

# backwards compatibility. Once nothing else refers to BaseWidget, delete this
BaseWidget = RequestWidgetHandler
