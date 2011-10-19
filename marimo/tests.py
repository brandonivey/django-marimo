import json
import re

from django.conf import settings
from django.http import Http404, HttpRequest
from django.utils.unittest import TestCase
from django import template

import mock

from marimo.views import MarimoRouter
from marimo.views import BaseWidget

class FailingWidget(object):
    def __call__(self, request, *args, **kwargs):
        raise Exception

    def on_error(e, data, request, *args, **kwargs):
        return {'status':'failed'}


widgets = {
        'test': lambda x,y,z: {'key':'value'},
        'failure': FailingWidget()
}

class TestTag(TestCase):
    def setUp(self):
        self.real_murl = getattr(settings, 'MARIMO_URL', None)
        settings.MARIMO_URL = '/thissite'
        self.context = template.Context()
        request = mock.Mock()
        request.marimo_widgets = []
        request.META = dict(PATH_INFO='/some/path')
        self.context['request'] = request
        self.context['marimo_widgets'] = request.marimo_widgets

    def tearDown(self):
        if self.real_murl is None:
            del settings.MARIMO_URL
        else:
            settings.MARIMO_URL = self.real_murl

    def test_tag(self):
        t = template.Template("""{% load marimo %} {% marimo test incontext "stringarg" k1=incontext k2="stringkwarg" %}""")
        self.context['incontext'] = 'incon'
        rendered = t.render(self.context)
        self.assertTrue(re.search(r'<div id="test_.+" class="marimo class"', rendered))
        self.assertEquals(len(self.context['marimo_widgets']), 1)

class TestRouterView(TestCase):
    def setUp(self):
        self.request = mock.Mock()
        self.router = MarimoRouter()

    def tearDown(self):
        pass

    def test_get(self):
        self.assertRaises(Http404, self.router.get, HttpRequest())

    @mock.patch('marimo.views.router._marimo_widgets', widgets)
    @mock.patch('marimo.views.router.HttpResponse')
    def test_route_success(self, http_response):
        bulk = [
                {'id':'1', 'widget_name':'test', 'args':['one', 'two'], 'kwargs':{}}
        ]
        self.router.route(self.request, bulk)
        response = json.loads(http_response.call_args[0][0])
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['status'], 'succeeded')
        self.assertEqual(response[0]['id'], '1')

    @mock.patch('marimo.views.router._marimo_widgets', widgets)
    @mock.patch('marimo.views.router.HttpResponse')
    def test_route_callable_fails(self, http_response):
        bulk = [
                {'id':'1', 'widget_name':'failure', 'args':['one', 'two'], 'kwargs':{}}
        ]
        self.router.route(self.request, bulk)
        response = json.loads(http_response.call_args[0][0])
        self.assertEquals(response[0]['status'], 'failed')

    @mock.patch('marimo.views.router._marimo_widgets', widgets)
    @mock.patch('marimo.views.router.HttpResponse')
    def test_route_no_such_widget(self, http_response):
        bulk = [
                {'id':'1', 'widget_name':'nopechucktesta', 'args':['one', 'two'], 'kwargs':{}}
        ]
        self.router.route(self.request, bulk)
        response = json.loads(http_response.call_args[0][0])
        self.assertEquals(response[0]['status'], 'WidgetNotFound')

    # TODO test fetching a callable with smart_import. this is too gnarly for now.

class TestBaseView(TestCase):
    def setUp(self):
        self.base = BaseWidget()
        self.base.template = 'some_template'
        self.base.cache_key = mock.Mock()
        self.base.cacheable = mock.Mock()
        self.base.uncacheable = mock.Mock()

    def tearDown(self):
        pass

    def test_base_no_use_cache(self):
        self.base.use_cache = False
        self.base('request', 'arg', kwarg='kwval')
        self.base.uncacheable.assert_called_with('request', {'context':dict(),'template':'some_template'},  'arg', kwarg='kwval')
        self.assertFalse(self.base.cacheable.called)

    @mock.patch('marimo.views.base.cache')
    def test_base_cache_miss(self, mock_cache):
        mock_cache.get.return_value = None
        self.base.use_cache = True
        self.base('request', 'arg', kwarg='kwval')
        self.assertTrue(mock_cache.set.called)
        self.assertTrue(self.base.cacheable.called)
        self.assertTrue(self.base.uncacheable.called)
    
    @mock.patch('marimo.views.base.cache')
    def test_base_cache_miss(self, mock_cache):
        self.base.use_cache = True
        self.base('request', 'arg', kwarg='kwval')
        self.assertFalse(self.base.cacheable.called)
        self.assertTrue(self.base.uncacheable.called)
