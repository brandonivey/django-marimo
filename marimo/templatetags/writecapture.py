import json
import random

from django import template

register = template.Library()

def jsescape(string):
    """ escaping so that javascript can be safely put into json dicts 
        for some reason json newline escaping isn't enough??
    """
    return string.replace('</script>','$ENDSCRIPT').replace('\n', '$NEWLINE').replace('\r','')

@register.tag(name='writecapture')
def write_capture(parser, token):
    """
        Syntax::
            {% writecapture ["prototype"] ["widget_id"] %}
                <script src="evil.js">
                    document.write('this is evil')
                <script>
            {% endwritecapture %}
    """
    # TODO should work with marimo fast and widget_id should be resolved maybe
    tokens = token.split_contents()
    nodelist = parser.parse(('endwritecapture',))
    parser.delete_first_token()
    if len(tokens) > 3:
        raise template.TemplateSyntaxError("writecapture block takes at most 2 arguments")
    return WriteCaptureNode(nodelist, *tokens[1:])

class WriteCaptureNode(template.Node):
    def __init__(self, nodelist, prototype='writecapture_widget', widget_id=None):
        self.nodelist = nodelist
        self.prototype = prototype
        self.widget_id = widget_id
        if not self.widget_id:
            self.widget_id = 'writecapture' + str(random.randint(0,99999999))

    def render(self, context):
        eviloutput = jsescape(self.nodelist.render(context))
        widget_dict = dict(widget_prototype=self.prototype, 
                            id=self.widget_id, 
                            html=eviloutput,
                            draw_events=[self.widget_id+"_ready"]
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
