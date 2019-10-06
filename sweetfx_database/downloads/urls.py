from django.conf.urls import url
from sweetfx_database.downloads import views

urlpatterns = [
        url(r'$', views.Downloads.as_view(), name="downloads-main"),
]