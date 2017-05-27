from django.conf.urls.defaults import patterns, url
from sweetfx_database.downloads import views

urlpatterns = patterns('',
    url(r'$', views.Downloads.as_view(), name="downloads-main"),
)
