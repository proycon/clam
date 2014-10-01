from django import VERSION
#from django.views.generic.simple import direct_to_template
from clamopener import settings

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

if VERSION[1] >= 6: #Django 1.6
    from django.conf.urls import patterns, url, include
    from django.conf.urls.static import static
else:
    from django.conf.urls.defaults import *

urlpatterns = patterns('',
    # Example:
    ('^/?$', 'clamopener.clamindex.views.index' ),
    ('^register/?$', 'clamopener.clamusers.views.register' ),
    ('^activate/([0-9]+)/?$', 'clamopener.clamusers.views.activate' ),
    ('^changepw/([0-9]+)/?$', 'clamopener.clamusers.views.changepw' ),
    ('^report/?$', 'clamopener.clamusers.views.report' ),
    ('^userlist/?$', 'clamopener.clamusers.views.userlist' ),
    #('^edit/', 'clamopener.views.edit' ),
    #(r'^admin/', include(admin.site.urls))
    (r'^style/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
)
