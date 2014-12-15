from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.views.decorators.cache import never_cache

import sign.views

urlpatterns = patterns('',
    url(r'^client', sign.views.xhr_client),
    url(r'^message', sign.views.xhr_message),

    url('^channel/(?P<channel_id>\d+)/relay', sign.views.xhr_channelrelay),
    url('^channel$', sign.views.xhr_channel),
    url('^log$', sign.views.xhr_logpost),
    url('^feedback$', sign.views.xhr_feedback),
)
