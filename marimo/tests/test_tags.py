import re

from django.conf import settings
from django.utils.unittest import TestCase
from django import template

import mock

from marimo.middleware import MarimoEventContainer


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

    def test_tag(self):
        t = template.Template("""{% load marimo %} {% marimo test incontext "stringarg" k1=incontext k2="stringkwarg" %}""")
        self.context['incontext'] = 'incon'
        rendered = t.render(self.context)
        self.assertTrue(re.search(r'<div id="test_.+" class="marimo class"', rendered))
        self.assertEquals(len(self.context['marimo_widgets']), 1)

    def test_writecapture_delay_tag_no_args(self):
        t = template.Template("""{% load writecapture %} {% writecapture_delay %}""")
        rendered = t.render(self.context)
        self.assertTrue("write_" in self.request.marimo_writecapture_delay.marimo_event)

    def test_writecapture_delay_tag_with_event(self):
        t = template.Template("""{% load writecapture %} {% writecapture_delay documentready %}""")
        rendered = t.render(self.context)
        self.assertTrue("documentready" in self.request.marimo_writecapture_delay.marimo_event)