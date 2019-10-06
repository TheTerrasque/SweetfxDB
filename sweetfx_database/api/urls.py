from django.conf.urls import url, include
from sweetfx_database.api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'games', views.GameViewSet)
router.register(r'presets', views.PresetViewSet)
router.register(r'screenshots', views.PresetScreenshotViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    #url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

