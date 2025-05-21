from rest_framework import serializers
from rest_framework.reverse import reverse
from sweetfx_database.gamedb import models as GM

class miniGameSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GM.Game
        fields = ("id", "title", "link")

class miniPresetSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GM.Preset
        fields = ("id", "title", "link", "screenshot_count")
        
class mPresetScreenshotSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GM.PresetScreenshot
        fields = ("image", "medium_thumb", "sweetfx_state", "link")

class PresetScreenshotSerializer(serializers.HyperlinkedModelSerializer):
    image = serializers.Field(source="image.url")
    comparison = serializers.SerializerMethodField('get_file_url_for_comparison')
    medium_thumb = serializers.Field(source="medium_thumb.url")
    sweetfx_state_description = serializers.Field(source="get_sweetfx_state_display")
    
    weblink = serializers.Field(source='get_absolute_url')
    preset = miniPresetSerializer()
    
    class Meta:
        model = GM.PresetScreenshot
        fields = ("id", "preset", "image", "image_height", "image_width", "created", "sweetfx_state", "sweetfx_state_description", "description", "comparison", "medium_thumb", "link", "weblink")

    def get_file_url_for_comparison(self, obj):
        if obj.comparison_image:
            return obj.comparison_image.url

class PresetSerializer(serializers.HyperlinkedModelSerializer):
    creator = serializers.Field(source="creator.username")
    shader = serializers.Field(source="shader.name")
    game = miniGameSerializer()
    weblink = serializers.Field(source='get_absolute_url')
    screenshots = mPresetScreenshotSerializer(source="presetscreenshot_set", many=True)
    class Meta:
        model = GM.Preset
        fields = ("id", "title", "added", "updated", "description", "settings_text", "game", "shader", "downloads", "screenshots", "link", "weblink")

class GameSerializer(serializers.HyperlinkedModelSerializer):
    creator = serializers.Field(source="creator.username")
    presets = miniPresetSerializer(many=True, source="get_presets")
    
    weblink = serializers.Field(source='get_absolute_url')
    class Meta:
        model = GM.Game
        fields = ("id", "title", "exename", "url", "creator", "added", "sweetfx_notes", "presets", "link", "weblink")
