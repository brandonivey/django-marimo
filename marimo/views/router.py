import json

from django.conf import settings
from django.http import Http404, HttpResponse
from django.views.generic.base import View

from marimo.utils import smart_import

try:
    _marimo_widgets = smart_import(settings.MARIMO_REGISTRY)
except AttributeError:
    _marimo_widgets = {}


class MarimoRouter(View):
    """
    MarimoRouter splits up the request into individual widget packages and
    sends them to the handlers defined int he MARIMO_REGISTY
    """

    # TODO store widget registry as class variable so it can be overidden in instances

    def get(self, request):
        """ for a get request the bulk data is in request.GET """
        try:
            bulk = json.loads(request.GET['bulk'])
        except KeyError:
            raise Http404()
        else:
            return self.route(request, bulk)

    def route(self, request, bulk):
        """ this actually does the routing """
        response = []
        nocache_override = None
        # TODO sanitize bulk
        for widget in bulk:
            # Clean kwargs; these are passed to python functions and can open
            # us up to basic string injection attacks. any sensitive args
            # (beginning with __) need to be stripped out. Also, there is a
            # hack (TODO) for for python < 2.6.6 which can't handle unicode strings as
            # dict keys when using them with **. It sucks.
            clean_widget_kwargs = {}
            for key in widget['kwargs'].keys():
                if not key.startswith('__'):
                    clean_widget_kwargs[str(key)] = widget['kwargs'][key]
            widget['kwargs'] = clean_widget_kwargs

            # Try to get a callable from the dict... if it's not imported deal with it
            data = { 'id': widget['id'], }
            try:
                # TODO widget_name -> widget_handler; also fall back to widget_id and widget_prototype in searching for handler.
                view = _marimo_widgets[widget['widget_name']]
            except KeyError:
                data['status'] = 'WidgetNotFound'
            else:
                if not callable(view):
                    view = smart_import(view)()
                    _marimo_widgets[widget['widget_name']] = view

                try:
                    data.update(view(request, *widget.get('args', []), **widget.get('kwargs', {})))
                    # req, args, kwargs -> dict
                    view_data = view(request, *widget.get('args', []), **widget.get('kwargs', {}))
                    if '__nocache_override' in view_data:
                        nocache_override = view_data['__nocache_override']
                        del view_data['__nocache_override']
                    data.update(view_data)
                except Exception, e:
                    data = view.on_error(e, data, request, *widget['args'], **widget['kwargs'])
                else:
                    data['status'] = 'succeeded'
            finally:
                response.append(data)

        return self.build_response(request, response, nocache_override)

    def build_response(self, request, data, nocache_override=None):
        as_json = json.dumps(data)
        if request.REQUEST.get('format') == 'jsonp' and request.REQUEST.get('callback'):
            content_type = 'text/javascript'
            callback = request.REQUEST.get('callback')
            as_json = "{0}({1});".format(callback, as_json)
        else:
            content_type = 'application/json'

        hresp = HttpResponse(as_json, content_type=content_type)
        if nocache_override:
            hresp['Cache-Control'] = nocache_override

        return hresp
