import mock

from django.utils.unittest import TestCase

from marimo.middleware import MarimoEventContainer, Marimo, context_processor


class TestMiddleware(TestCase):
    def setUp(self):
        self.middleware = Marimo()

    def tearDown(self):
        del self.middleware

    def test_process_request_marimo_widgets_added(self):
        req = mock.Mock()
        self.middleware.process_request(req)
        self.assertTrue(isinstance(req.marimo_widgets, list))

    def test_process_request_marimo_writecapture_delay_added(self):
        req = mock.Mock()
        self.middleware.process_request(req)
        self.assertTrue(isinstance(req.marimo_writecapture_delay,
                                   MarimoEventContainer))

    def test_process_response_marimo_widgets_added(self):
        req = mock.Mock()
        req.marimo_writecapture_delay = MarimoEventContainer()
        req.marimo_widgets = ['dummywidget']
        resp = mock.Mock()
        resp.content = "dummytext ${MARIMO} moredumbtext"
        self.middleware.process_response(req, resp)
        self.assertTrue("dummywidget" in resp.content)

    def test_process_response_marimo_writecapture_delay_added(self):
        req = mock.Mock()
        req.marimo_widgets = []
        req.marimo_writecapture_delay = MarimoEventContainer("documentready")
        resp = mock.Mock()
        resp.content = "dummytext ${MARIMO} moredumbtext"
        self.middleware.process_response(req, resp)
        self.assertTrue("documentready" in resp.content)


class TestContextProcessor(TestCase):
    def setUp(self):
        self.request = mock.Mock()
        self.request.marimo_widgets = ['dummywidget']
        self.request.marimo_writecapture_delay = MarimoEventContainer()

    def tearDown(self):
        del self.request

    def test_marimo_widgets_added_to_context(self):
        extra_context = context_processor(self.request)
        self.assertEqual(extra_context["marimo_widgets"],
                         self.request.marimo_widgets)

    def test_marimo_writecapture_delay_added_to_context(self):
        extra_context = context_processor(self.request)
        self.assertEqual(extra_context["marimo_writecapture_delay"],
                         self.request.marimo_writecapture_delay)
