import json
import re

# TODO: this seems like it should be a django setting
MARIMO_PLACEHOLDER = re.compile("\$\{MARIMO\}")

class Marimo(object):
    """ 
    a simple middleware to register all widgets during page generation
    and add a script to load them where "${MARIMO}" is in the page
    """
    def process_request(self, request):
        """ sticks marimo_widgets in the request """
        request.marimo_widgets = []
        # we use a list here and only touch the first element
        # this is merely so that we can tweak values in it by reference
        # TODO: consider making some sort of marimo context objects to
        # track all of this stuff
        request.marimo_writecapture_delay = []

    def process_response(self, request, response):
        """ generates a script to register and load the widgets with marimo """
        # TODO: check to maker sure the placeholder exists
        # TODO: add_widgets shouldn't make the request
        if not hasattr(request, 'marimo_widgets'):
            # skip this
            return response
        code = "marimo.add_widgets(%s);" %json.dumps(request.marimo_widgets)

        if getattr(request, 'marimo_writecapture_delay', False):
            # TODO this should concat not replace
            code = "marimo.widgetlib.writecapture_widget.render_events = ['%s'];" % request.marimo_writecapture_delay[0] + code

        response.content = MARIMO_PLACEHOLDER.sub(code, response.content)
        return response

def context_processor(request):
    """ sticks marimo_widgets into the template context """
    extra_context = {}
    if hasattr(request, 'marimo_widgets'):
        extra_context['marimo_widgets'] = request.marimo_widgets
    if hasattr(request, 'marimo_writecapture_delay'):
        extra_context['marimo_writecapture_delay'] = request.marimo_writecapture_delay
    return extra_context
