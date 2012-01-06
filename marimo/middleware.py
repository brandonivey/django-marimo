import json
import re

# TODO: these seem like they should be django settings
MARIMO_PLACEHOLDER = re.compile("\$\{MARIMO\}")
SLOW_EVENT = "dombodyloaded"


class MarimoEventContainer(object):
    """
    Holds a marimo event to be shared between request attributes
    and template context.

    """
    # TODO: currently this accommodates the event for the writecapture_delay
    # tag, consider making the container more generic
    def __init__(self, marimo_event=None):
        self.marimo_event = marimo_event


class Marimo(object):
    """
    a simple middleware to register all widgets during page generation
    and add a script to load them where "${MARIMO}" is in the page
    """
    def process_request(self, request):
        """ sticks marimo_widgets in the request """
        request.marimo_widgets = []
        request.marimo_writecapture_delay = MarimoEventContainer()
        request.marimo_slow = False

    def process_response(self, request, response):
        """ generates a script to register and load the widgets with marimo """
        # TODO: check to maker sure the placeholder exists
        # TODO: add_widgets shouldn't make the request
        if not hasattr(request, 'marimo_widgets'):
            # skip this
            return response
        code = "marimo.add_widgets(%s);" %json.dumps(request.marimo_widgets)

        wc_delay = getattr(request, 'marimo_writecapture_delay')
        if wc_delay.marimo_event:
            code = "marimo.widgetlib.writecapture_widget.render_events = " \
                   "['%s'];%s" % (wc_delay.marimo_event, code)
        if getattr(request, 'marimo_slow', False):
            # TODO this should concat not replace
            code = "marimo.widgetlib.writecapture_widget.render_events = ['%s'];" % SLOW_EVENT + code

        response.content = MARIMO_PLACEHOLDER.sub(code, response.content)
        return response

def context_processor(request):
    """ sticks marimo_widgets into the template context """
    extra_context = {}
    if hasattr(request, 'marimo_widgets'):
        extra_context['marimo_widgets'] = request.marimo_widgets
    if hasattr(request, 'marimo_writecapture_delay'):
        extra_context['marimo_writecapture_delay'] = request.marimo_writecapture_delay
    if hasattr(request, 'marimo_slow'):
        extra_context['marimo_slow'] = request.marimo_slow
    return extra_context
