from django.conf.urls import url
from sweetfx_database.users import views

urlpatterns = [
    url(r'u/(?P<slug>.+)/$', views.UserDetail.as_view(), name="user-detail"),
    url(r'remove_user/$', views.remove_user, name="user-nuke"),
    url(r'alerts/$', views.UserAlerts.as_view(), name="user-alerts"),
    url(r'profile/$', views.UserProfile.as_view(), name="user-profile"),
    url(r'favorites/add/$', views.add_preset_to_favorite, name="user-addfav"),
    url(r'favorites/$', views.PresetFavorites.as_view(), name="user-favs"),
    url(r'favorites/remove/$', views.remove_preset_from_favorite, name="user-rmfav"),
]
