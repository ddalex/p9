from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView
from django.views.decorators.cache import never_cache

# Uncomment the next two lines to enable the admin:
from django.contrib import admin, auth
admin.autodiscover()

import sign.views

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'sign.views.home', name='home'),
    # url(r'^p9/', include('p9.foo.urls')),
    url(r'^channelcreate', sign.views.channelcreate),
    url(r'^channelview/(?P<channelid>\d+)/', sign.views.channelview),
    url(r'^api/1.0/', include ('sign.api1urls')),


    # own administration
    url("^accounts/login/", 'django.contrib.auth.views.login', { 'template_name': 'admin/login.html'}),
    url("^accounts/logout/", 'django.contrib.auth.views.logout' ),
    url("^oview$", sign.views.oview),
    url('^log$', sign.views.log),


    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),

    # redirect all 404
    url(r'.*', never_cache(RedirectView.as_view(url = "/"))),
    
)
