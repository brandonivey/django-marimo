from django.conf.urls.defaults import patterns, url

from marimo.views.router import MarimoRouter 

urlpatterns = patterns('',
    url(r'^$', MarimoRouter.as_view()),
)
