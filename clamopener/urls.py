from django.conf.urls.defaults import *
from clamopener import settings

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    ('^/?$', 'clamopener.clamusers.views.register' ),      
    ('^activate/([0-9]+)/?$', 'clamopener.clamusers.views.activate' ),     
    #('^edit/', 'clamopener.views.edit' ),
    #(r'^admin/', include(admin.site.urls))
    (r'^style/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
)
