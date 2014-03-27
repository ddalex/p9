from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.views.decorators.cache import never_cache

import sign.views

urlpatterns = patterns('',
    url(r'^client', 'sign.views.xhr_client'),
    url(r'^message', 'sign.views.xhr_message'),

    url('^channeladd', sign.views.xhr_channeladd),
    url('^channeldel', sign.views.xhr_channeldel),
    url('^channellist', sign.views.xhr_channellist),
    url('^channelrelayadd', sign.views.xhr_channelrelayadd),
    url('^channelrelaydel', sign.views.xhr_channelrelaydel),
    url('^channelrelaylist', sign.views.xhr_channelrelaylist),
    
)
