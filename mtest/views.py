from django.template import RequestContext
from django.shortcuts import render_to_response

from marimo.views.base import BaseWidget
from marimo.template_loader import template_loader


def main(request):
    return render_to_response('main.html', RequestContext(request))

class TestWidget(BaseWidget):
    #template = 'hello {{ name }} are you {{ status }}? if not i will {{ action }} you.'
    template = template_loader.load('test_widget.html')
    use_cache = True

    def cache_key(self, *args, **kwargs):
        return 'test_widget:%s' % args[0]

    def cacheable(self, response, *args, **kwargs):
        response['context']['name'] = args[0]
        response['context']['status'] = 'blue'
        return response

    def uncacheable(self, request, response, *args, **kwargs):
        response['context']['action'] = args[1]
        return response
