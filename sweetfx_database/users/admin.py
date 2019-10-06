from . import models as M
from django.contrib import admin
from reversion import admin as reversion

class Profile(reversion.VersionAdmin):
    list_display = ["user"]
    search_fields = ["user__username"]

class Theme(reversion.VersionAdmin):
    list_display = ["title", "default"]
    search_fields = ["title"]

class PresetFavorite(reversion.VersionAdmin):
    list_display = ["preset", "user"]

admin.site.register(M.UserProfile, Profile)
admin.site.register(M.Theme, Theme)

admin.site.register(M.PresetFavorite, PresetFavorite)
