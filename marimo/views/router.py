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
        # TODO sanitize bulk
        for widget in bulk:
            print "doing: %s"%widget['id']
            # Try to get a callable from the dict... if it's not imported deal with it
            data = { 'id': widget['id'], }
            try:
                view = _marimo_widgets[widget['widget_name']]
            except KeyError:
                print widget['widget_name']
                print _marimo_widgets
                data['status'] = 'WidgetNotFound'
            else:
                if not callable(view):
                    view = smart_import(view)()
                    _marimo_widgets[widget['widget_name']] = view

                try:
                    data.update(view(request, *widget['args'], **widget['kwargs']))
                except Exception, e:
                    data = view.on_error(e, data, request, *widget['args'], **widget['kwargs'])
                else:
                    data['status'] = 'succeeded'
            finally:
                response.append(data)

        return self.build_response(request, response)

    def build_response(self, request, data):
        as_json = json.dumps(data)
        if request.REQUEST.get('format') == 'jsonp' and request.REQUEST.get('callback'):
            mimetype = 'text/javascript'
            callback = request.REQUEST.get('callback')
            as_json = "{0}({1});".format(callback, as_json)
        else:
            mimetype = 'application/json'

        return HttpResponse(as_json, mimetype=mimetype)
