from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    ('^/?$', 'clamopener.views.register' ),      
    ('^activate/([0-9]+)/?$', 'clamopener.views.activate' ),     
    #('^edit/', 'clamopener.views.edit' ),
    #(r'^admin/', include(admin.site.urls))
)
