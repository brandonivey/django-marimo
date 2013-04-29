import json

from django.http import Http404, HttpRequest
from unittest2 import TestCase

import mock

from marimo.template_loader import TemplateNotFound
from marimo.views import MarimoRouter
from marimo.views import BaseWidget, RequestWidgetHandler

class FailingWidget(object):
    def __call__(self, request, *args, **kwargs):
        raise Exception

    def on_error(e, data, request, *args, **kwargs):
        return {'status':'failed'}


widgets = {
        'test': lambda x,y,z: {'key':'value'},
        'failure': FailingWidget()
}


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
        self.base.uncacheable = mock.Mock()

    def tearDown(self):
        pass

    def test_base_no_use_cache(self):
        # when cache is not used, we still call both cacheable and uncacheable;
        # cacheable is what sets the template into the context
        self.base.cache_key = lambda *a, **kw: None
        self.base('request', 'arg', kwarg='kwval')
        self.base.uncacheable.assert_called_with('request', {'context':dict(), 'template': 'some_template'}, 'arg', kwarg='kwval')

    @mock.patch('marimo.views.base.cache')
    def test_base_cache_miss(self, mock_cache):
        # On a cache miss, both cacheable and uncacheable will be called, and
        # the cache will be set.
        self.base.cacheable = mock.Mock()
        self.base.cache_key = lambda *a, **kw: 'key'
        mock_cache.get.return_value = None
        self.base('request', 'arg', kwarg='kwval')
        self.assertTrue(mock_cache.set.called)
        self.assertTrue(self.base.cacheable.called)
        self.assertTrue(self.base.uncacheable.called)

    @mock.patch('marimo.views.base.cache')
    def test_base_cache_hit(self, mock_cache):
        # On a cache hit, only uncacheable will be called.
        self.base.cacheable = mock.Mock()
        self.base.cache_key = lambda *a, **kw: 'key'
        mock_cache.get.return_value = 'something'
        self.base('request', 'arg', kwarg='kwval')
        self.assertFalse(self.base.cacheable.called)
        self.assertTrue(self.base.uncacheable.called)

    def test_nocache_override(self):
        response = dict()
        self.base.nocache_override(response)
        self.assertTrue('__nocache_override' in response)
        self.assertEqual(response['__nocache_override'], 'no-cache,max-age=0')

class TestRequestWidgetHandlerView(TestCase):
    def setUp(self):
        self.handler = RequestWidgetHandler()
        self.handler.template = 'some template code'

    def test_default_resposne_template_not_found(self):
        mtpl = mock.Mock()
        mtpl.load = mock.Mock(side_effect=TemplateNotFound)
        with mock.patch('marimo.views.base.template_loader', mtpl):
            template_path = 'hello'
            response = self.handler.default_response(**{'template_path':template_path})
        self.assertEqual(response['template'], self.handler.template)

    def test_base_default_response_template(self):
        with mock.patch('marimo.views.base.template_loader') as mtpl:
            template_path = 'hello'
            self.handler.default_response(**{'template_path':template_path})

        mtpl.load.assert_called_with(template_path)

    def test_base_default_response_no_template(self):
        with mock.patch('marimo.views.base.template_loader') as mtpl:
            self.handler.default_response()

        self.assertTrue(not mtpl.called)
