from . import models as M
from django.contrib import admin
from reversion import admin as reversion

class Preset(reversion.VersionAdmin):
    list_display = ["title", "creator", "game"]
    list_filter = ["visible"]
    date_hierarchy = "added"
    search_fields = ["title", "creator__username", "game__title"]
    raw_id_fields = ["creator", "game"]

class Comment(reversion.VersionAdmin):
    list_filter = ["visible", "content_type"]
    list_display = ["creator", "content_type", "visible", "added", "get_text_start"]
    search_fields = ["creator__username", "comment"]
    date_hierarchy = "added"
    raw_id_fields = ["creator"]

class Screenshot(reversion.VersionAdmin):
    list_filter = ["visible"]
    search_fields = ["creator__username", "preset__title"]
    raw_id_fields = ["preset", "creator"]

class Game(reversion.VersionAdmin):
    list_display = ["title", "creator"]
    list_filter = ["visible"]
    date_hierarchy = "added"
    search_fields = ["title", "creator__username"]
    raw_id_fields = ["creator"]

class Shader(reversion.VersionAdmin):
    list_display = ["name", "description", "url"]
   

admin.site.register(M.UserComment, Comment)
admin.site.register(M.Game, Game)
admin.site.register(M.Shader, Shader)
admin.site.register(M.Preset, Preset)
admin.site.register(M.PresetScreenshot, Screenshot)
