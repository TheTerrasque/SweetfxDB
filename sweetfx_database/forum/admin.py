from . import models as M
from django.contrib import admin
from reversion import admin as reversion

class ForumThread(reversion.VersionAdmin):
    list_display = ["title", "creator", "posts"]
    search_fields = ["title", "creator__username"]
    raw_id_fields = ["creator", "last_post"]

class ForumPost(reversion.VersionAdmin):
    list_display = ["creator", "thread", "created"]
    search_fields = ["text", "creator__username"]
    raw_id_fields = ["creator", "thread"]

admin.site.register(M.Forum)
admin.site.register(M.ForumThread, ForumThread)
admin.site.register(M.ForumPost, ForumPost)
