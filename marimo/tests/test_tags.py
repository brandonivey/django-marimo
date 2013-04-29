from functools import partial
import re

from django.conf import settings
from unittest2 import TestCase
from django import template

from mock import Mock, patch

from marimo.middleware import MarimoEventContainer
from marimo.templatetags.writecapture import write_capture


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
        request = Mock()
        request.marimo_widgets = []
        request.marimo_writecapture_delay = MarimoEventContainer()
        request.META = dict(PATH_INFO='/some/path')
        self.request = request
        self.context['request'] = request
        self.context['marimo_widgets'] = request.marimo_widgets
        self.context['marimo_writecapture_delay'] = request.marimo_writecapture_delay

    def tearDown(self):
        if self.real_murl is None:
            del settings.MARIMO_URL
        else:
            settings.MARIMO_URL = self.real_murl

    def test_marimo_tag(self):
        t = template.Template("""{% load marimo %} {% marimo test incontext "stringarg" k1=incontext k2="stringkwarg" %}""")
        self.context['incontext'] = 'incon'
        settings.MARIMO_FAST = False
        rendered = t.render(self.context)
        self.assertTrue(re.search(r'<div id="test_.+" class="marimo class"', rendered))
        self.assertEquals(len(self.context['marimo_widgets']), 0)
        settings.MARIMO_FAST = True
        t.render(self.context)
        self.assertEquals(len(self.context['marimo_widgets']), 1)

    def test_writecapture_delay_tag_no_args(self):
        t = template.Template("""{% load writecapture %} {% writecapture_delay %}""")
        t.render(self.context)
        self.assertTrue("write_" in self.request.marimo_writecapture_delay.marimo_event)

    def test_writecapture_delay_tag_with_event(self):
        t = template.Template("""{% load writecapture %} {% writecapture_delay documentready %}""")
        t.render(self.context)
        self.assertTrue("documentready" in self.request.marimo_writecapture_delay.marimo_event)

class TestWritecaptureTag(TestCase):
    compat_true_re = '.*wc_compatibility_mode.*true'
    compat_false_re = '.*wc_compatibility_mode.*false'
    mock_jsescape = Mock(return_value='content')
    match = lambda regex, string: bool(re.match(regex, string, re.S))
    match_true = partial(match, compat_true_re)
    match_false = partial(match, compat_false_re)

    def assertScriptFilterOn(self, string):
        self.assertTrue(self.match_true(string))
        self.assertFalse(self.match_false(string))

    def assertScriptFilterOff(self, string):
        self.assertFalse(self.match_true(string))
        self.assertTrue(self.match_false(string))

    def assertIdExists(self, output):
        self.assertTrue('id="writecapture' in output)

    def assertPrototype(self, prototype, string):
        self.assertTrue(bool(re.match('.*widget_prototype.*%s' % prototype, string, re.S)))

    def setUp(self):
        def run(*tokens):
            mock_parser = Mock()
            mock_token = Mock()
            mock_token.split_contents.return_value= ['writecapture'] + list(tokens)
            return write_capture(mock_parser, mock_token)
        self.run = run
        self.stub_context = { 'wc_compatibility_mode': None }


    @patch('marimo.templatetags.writecapture.jsescape', mock_jsescape)
    def test_writecapture_tag_no_args(self):
        output = self.run().render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOff(output)

    @patch('marimo.templatetags.writecapture.jsescape', mock_jsescape)
    def test_writecapture_tag_script_filter_literal(self):
        output = self.run('False').render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOff(output)

        output = self.run('True').render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOn(output)

    @patch('marimo.templatetags.writecapture.jsescape', mock_jsescape)
    def test_writecapture_tag_script_filter_var_set(self):
        self.stub_context['a_variable'] = True
        output = self.run('a_variable').render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOn(output)

        self.stub_context['a_variable'] = False
        output = self.run('a_variable').render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOff(output)

    @patch('marimo.templatetags.writecapture.jsescape', mock_jsescape)
    def test_writecapture_tag_script_filter_var_None(self):
        self.stub_context['a_variable'] = None
        output = self.run('a_variable').render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOff(output)

    @patch('marimo.templatetags.writecapture.jsescape', mock_jsescape)
    def test_writecapture_global_script_filter(self):
        self.stub_context['wc_compatibility_mode'] = True
        output = self.run('False').render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOn(output)

    @patch('marimo.templatetags.writecapture.jsescape', mock_jsescape)
    def test_writecapture_tag_two_args(self):
        output = self.run('False', 'some_prototype').render(self.stub_context)

        self.assertIdExists(output)
        self.assertScriptFilterOff(output)
        self.assertPrototype('some_prototype', output)

    @patch('marimo.templatetags.writecapture.jsescape', mock_jsescape)
    def test_writecapture_tag_three_args(self):
        output = self.run('False', 'some_prototype', 'dealWithIt').render(self.stub_context)

        self.assertTrue('id="dealWithIt"' in output)
        self.assertScriptFilterOff(output)
        self.assertPrototype('some_prototype', output)
