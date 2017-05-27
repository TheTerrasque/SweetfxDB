from django.conf.urls import patterns, include, url
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', RedirectView.as_view(url="/games/"), name='home'),
    url(r'^games/', include('sweetfx_database.gamedb.urls')),
    url(r'^silly/', include('sweetfx_database.silly.urls')),
    url(r'^users/', include('sweetfx_database.users.urls')),
    url(r'^forum/', include('sweetfx_database.forum.urls')),
    url(r'^downloads/', include('sweetfx_database.downloads.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    (r'^accounts/', include('registration.backends.default.urls')),
    #(r'^account/', include('django_authopenid.urls')),
    url(r'^api/', include('sweetfx_database.api.urls')),
)
