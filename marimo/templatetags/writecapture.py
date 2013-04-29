import json
import random

from django import template

import logging
logger = logging.getLogger(__name__)

register = template.Library()

def jsescape(string):
    """ escaping so that javascript can be safely put into json dicts
        for some reason json newline escaping isn't enough??
    """
    return string.replace('<script','$BEGINSCRIPT').replace('</script>','$ENDSCRIPT').replace('\n', '$NEWLINE').replace('\r','')

@register.tag(name='writecapture')
def write_capture(parser, token):
    """
        Syntax::
            {% writecapture [filter] ["prototype"] ["widget_id"] %}
                <script src="evil.js">
                    document.write('this is evil')
                <script>
            {% endwritecapture %}

        Wraps the enclosed HTML inside of a marimo writecapture widget.

        The ``filter`` argument is a boolean (default False) that turns on a
        writecapture feature called writeOnGetElementById. This fixes some
        extra-bad scripts.

        The ``prototype`` argument defaults to 'writecapture.' You will only
        need to use this if you have subclassed marimo's built-in writecapture
        widget and want to use that instead.

        The ``widget_id`` argument defaults to a 'writecapture_<randomnumber>.'
        Use this only if you need to specify an alternate element id in the DOM
        to write to (otherwise one will be created for you at the site of the
        {%writecapture%} invocation)..

    """
    # TODO should work with marimo fast and widget_id should be resolved maybe
    tokens = token.split_contents()
    if len(tokens) > 4:
        raise template.TemplateSyntaxError("writecapture block takes at most 3 arguments")
    nodelist = parser.parse(('endwritecapture',))
    parser.delete_first_token()

    if len(tokens) > 1:
        script_filter = tokens[1]
        if script_filter == 'False':
            script_filter = False
        elif script_filter == 'True':
            script_filter = True
        else:
            script_filter = template.Variable(script_filter)
    else:
        script_filter = False

    return WriteCaptureNode(nodelist, script_filter, *tokens[2:])

class WriteCaptureNode(template.Node):
    def __init__(self, nodelist, script_filter=False, prototype='writecapture_widget', widget_id=None):
        self.nodelist = nodelist
        self.script_filter = script_filter
        self.prototype = prototype
        self.widget_id = widget_id
        if not self.widget_id:
            self.widget_id = 'writecapture' + str(random.randint(0,99999999))

    def render(self, context):
        eviloutput = jsescape(self.nodelist.render(context))
        if isinstance(self.script_filter, template.Variable):
            self.script_filter = bool(self.script_filter.resolve(context))
        # Set this flag in your template tag for advanced write capture widget sanitation.
        # Source: https://github.com/iamnoah/writeCapture/wiki/Usage

        global_compatibility_mode = context.get('wc_compatibility_mode', None)
        if global_compatibility_mode is None:
            wc_compatibility_mode = self.script_filter
        else:
            wc_compatibility_mode = global_compatibility_mode

        widget_dict = dict(widget_prototype=self.prototype,
                            id=self.widget_id,
                            html=eviloutput,
                            wc_compatibility_mode = wc_compatibility_mode,
                         )
        output = """<div id="{widget_id}"></div>
<script type="text/javascript">
    marimo.emit('{widget_id}_ready');
    marimo.add_widget({widget_json});
</script>"""
        output = output.format(
            widget_id=self.widget_id,
            widget_json=json.dumps(widget_dict),
        )
        return output

@register.tag(name='writecapture_delay')
def write_capture_delay(parser, token):
    """
        Syntax::
            {% writecapture_delay [event_name] %}
    """
    tokens = token.split_contents()
    if len(tokens) > 2:
        raise template.TemplateSyntaxError("writecapture_delay takes at most 1 argument")
    if len(tokens) == 2:
        return WriteCaptureDelayNode(tokens[1])
    return WriteCaptureDelayNode()

class WriteCaptureDelayNode(template.Node):
    def __init__(self, event=None):
        self.event = event

    def render(self, context):
        output = ''
        if self.event is None:
            self.event = 'write_' + str(random.randint(0,999999))
            output = """<script type="text/javascript">marimo.emit('%s');</script>""" % self.event

        # this should only be used once per page if it's uses a second time
        # overwrite but log an error
        wc_delay = context.get('marimo_writecapture_delay', None)
        if not wc_delay:
            logger.error("The writecapture_delay was called but didn't find "
                         "marimo_writecapture_delay in the context. The tag "
                         "depends on the Marimo middleware and context_processor.")
            return output
        if wc_delay.marimo_event:
            logger.error('Overwriting the marimo event delay %s with %s' %
                         (wc_delay.marimo_event, self.event))
        wc_delay.marimo_event = self.event
        return output

@register.tag(name='writecapture_delay')
def write_capture_delay(parser, token):
    """
        Syntax::
            {% writecapture_delay [event_name] %}
    """
    tokens = token.split_contents()
    if len(tokens) > 2:
        raise template.TemplateSyntaxError("writecapture_delay takes at most 1 argument")
    if len(tokens) == 2:
        return WriteCaptureDelayNode(tokens[1])
    return WriteCaptureDelayNode()

class WriteCaptureDelayNode(template.Node):
    def __init__(self, event=None):
        self.event = event

    def render(self, context):
        output = ''
        if self.event is None:
            self.event = 'write_' + str(random.randint(0,999999))
            output = """<script type="text/javascript">marimo.emit('%s');</script>""" % self.event

        # this should only be used once per page if it's uses a second time
        # overwrite but log an error
        wc_delay = context.get('marimo_writecapture_delay', None)
        if not wc_delay:
            logger.error("The writecapture_delay was called but didn't find "
                         "marimo_writecapture_delay in the context. The tag "
                         "depends on the Marimo middleware and context_processor.")
            return output
        if wc_delay.marimo_event:
            logger.error('Overwriting the marimo event delay %s with %s' %
                         (wc_delay.marimo_event, self.event))
        wc_delay.marimo_event = self.event
        return output

@register.tag(name='writecapture_delay')
def write_capture_delay(parser, token):
    """
        Syntax::
            {% writecapture_delay [event_name] %}
    """
    tokens = token.split_contents()
    if len(tokens) > 2:
        raise template.TemplateSyntaxError("writecapture_delay takes at most 1 argument")
    if len(tokens) == 2:
        return WriteCaptureDelayNode(tokens[1])
    return WriteCaptureDelayNode()

class WriteCaptureDelayNode(template.Node):
    def __init__(self, event=None):
        self.event = event

    def render(self, context):
        output = ''
        if self.event is None:
            self.event = 'write_' + str(random.randint(0,999999))
            output = """<script type="text/javascript">marimo.emit('%s');</script>""" % self.event

        # this should only be used once per page if it's uses a second time
        # overwrite but log an error
        wc_delay = context.get('marimo_writecapture_delay', None)
        if not wc_delay:
            logger.error("The writecapture_delay was called but didn't find "
                         "marimo_writecapture_delay in the context. The tag "
                         "depends on the Marimo middleware and context_processor.")
            return output
        if wc_delay.marimo_event:
            logger.error('Overwriting the marimo event delay %s with %s' %
                         (wc_delay.marimo_event, self.event))
        wc_delay.marimo_event = self.event
        return output
