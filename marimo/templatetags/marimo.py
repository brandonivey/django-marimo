import json
import random

from django import template
from django.conf import settings

register = template.Library()

# TODO allow template tag to accept a string for widget constructor eg AdWidget

@register.tag(name="marimo")
def marimo(parser, token):
    """
        Syntax::
            {% marimo widget_name prototype [murl=http://some.url.com] [args] [kwargs] %}

        Examples::
            {% marimo comments request_widget objectpk=23 %}
    """
    tokens = token.split_contents()
    if len(tokens) < 3:
        raise template.TemplateSyntaxError('Need at least a widget_name and widget prototype')

    tokens.pop(0)
    widget_name = tokens.pop(0)
    prototype = tokens.pop(0)
    args = []
    kwargs = {}

    for token in tokens:
        parts = token.split('=')
        if len(parts) == 1:
            args.append(parts[0])
        elif len(parts) == 2:
            kwargs[parts[0]] = parts[1]
        else:
            raise template.TemplateSyntaxError('Arguments cannot contain =')

    return MarimoNode(widget_name, prototype, args, kwargs)

class MarimoNode(template.Node):
    def __init__(self, widget_name, prototype, args, kwargs):
        self.widget_name = widget_name
        self.prototype = prototype
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        if hasattr(self.kwargs, 'murl'):
            murl = self.kwargs.pop('murl')
        else:
            murl = settings.MARIMO_URL

        def maybe_resolve(arg):
            if arg[0] == '"' and arg[-1] == '"':
                return arg.strip('"')
            else:
                var = template.Variable(arg)
                return str(var.resolve(context))

        data = {}
        data['kwargs'] = {}
        for (k,v) in self.kwargs.items():
            data['kwargs'][k] = maybe_resolve(v)
        data['args'] = [maybe_resolve(arg) for arg in self.args]
        data['widget_name'] = self.widget_name
        data['id'] = self.generate_id()
        data['murl'] = murl
        data['widget_prototype'] = self.prototype

        divstr = '<div id="{id}" class="{cls}"></div>'.format(
           cls = getattr(settings, 'MARIMO_CLASS', 'marimo class'),
           id = data['id']
        )
        # TODO this is what needs to get written out by middleware...into head
        if (getattr(settings, 'MARIMO_FAST', False)):
            context['marimo_widgets'].append(data)
            script = ''
        else:
            script = '<script> marimo.add_widget(%s); </script>' % json.dumps(data)

        return divstr + script

    def generate_id(self):
        """ a widget's id is its name + a randint """
        # hopefully this is adequate
        return '%s_%s' % (self.widget_name, str(random.randint(0,999999)))
