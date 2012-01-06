import json
import re

MARIMO_PLACEHOLDER = re.compile("\$\{MARIMO\}")

class Marimo(object):
    """ 
    a simple middleware to register all widgets during page generation
    and add a script to load them where "${MARIMO}" is in the page
    """
    def process_request(self, request):
        """ sticks marimo_widgets in the request """
        request.marimo_widgets = []
        request.marimo_slow = False

    def process_response(self, request, response):
        """ generates a script to register and load the widgets with marimo """
        # TODO: check to maker sure the placeholder exists
        # TODO: add_widgets shouldn't make the request
        if not hasattr(request, 'marimo_widgets'):
            # skip this
            return response
        code = "marimo.add_widgets(%s);" %json.dumps(request.marimo_widgets)

        if getattr(request, 'marimo_slow', False):
            # TODO find slow event and this should concat not replace
            code = "marimo.widgetlib.writecapture_widget.render_events = [%s];" % SLOW_EVENT + code

        response.content = MARIMO_PLACEHOLDER.sub(code, response.content)
        return response

def context_processor(request):
    """ sticks marimo_widgets into the template context """
    extra_context = {}
    if hasattr(request, 'marimo_widgets'):
        extra_context['marimo_widgets'] = request.marimo_widgets
    if hasattr(request, 'marimo_slow'):
        extra_context['marimo_slow'] = request.marimo_slow
    return extra_context
