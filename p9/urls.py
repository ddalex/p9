from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.views.decorators.cache import never_cache

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

import sign.views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'sign.views.home', name='home'),
    url(r'^accounts/', include('allaccess.urls')),
    # url(r'^p9/', include('p9.foo.urls')),
    url(r'^channelcreate', sign.views.channelcreate),
    url(r'^channelview/(?P<channelid>\d+)/', sign.views.channelview),
    url(r'^api/1.0/', include ('sign.api1urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    #url(r'.*', never_cache(RedirectView.as_view(url="/static/index.html"))),
    
)
