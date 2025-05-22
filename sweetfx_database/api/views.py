from sweetfx_database.api import serializers as S
from sweetfx_database.gamedb import models as GM
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import filters

# Create your views here.

from rest_framework import viewsets

class SeparateViewSet(viewsets.ReadOnlyModelViewSet):
    # list, retrieve
    serializers = { 
        'default': None,
    }
    querysets = {
        #'default': None,
    }
    
    def get_serializer_class(self):
        return self.serializers.get(self.action,
                        self.serializers['default'])
    
    def get_queryset(self):
        return self.querysets.get(self.action,
                        self.queryset)
                        
class GameViewSet(SeparateViewSet):
    """
    List the active games in the database
    
    * games/newest/ lists presets sorted by added
    """
    serializers = { 
        'default': S.miniGameSerializer,
        'retrieve': S.GameSerializer,
    }
    
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('title', 'exename')
    ordering_fields = ('id', 'added', "preset_count", "title")
    
    queryset = GM.Game.active.all()
    
    querysets = {
        'retrieve': GM.Game.active.all().select_related("preset_set"),
    }

    @action(detail=False)
    def newest(self, request):
        recent_presets = self.get_queryset().order_by('-id')
        page = self.paginate_queryset(recent_presets)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)

class PresetViewSet(SeparateViewSet):
    """
    List the active presets in the database
    
    * presets/newest/ lists presets sorted by added
    """
    queryset = GM.Preset.active.all()#.select_related("game", "presetscreenshot_set")
    
    filter_backends = (filters.SearchFilter, filters.OrderingFilter)
    search_fields = ('game__title', 'title')
    ordering_fields = ('id', 'added', "preset_count", "title", "updated", "screenshot_count")
    
    serializers = { 
        'default': S.miniPresetSerializer,
        'retrieve': S.PresetSerializer,
    }

    querysets = {
        'retrieve': GM.Preset.active.all().select_related("game", "presetscreenshot_set"),
    }

    @action(detail=False)
    def newest(self, request):
        recent_presets = self.get_queryset().order_by('-id')
        page = self.paginate_queryset(recent_presets)
        serializer = self.get_pagination_serializer(page)
        return Response(serializer.data)

class PresetScreenshotViewSet(SeparateViewSet):
    queryset = GM.PresetScreenshot.active.all()
    querysets = {
        'retrieve': GM.PresetScreenshot.active.all().select_related("preset"),
    }
    serializers = { 
        'default': S.mPresetScreenshotSerializer,
        'retrieve': S.PresetScreenshotSerializer,
    }
