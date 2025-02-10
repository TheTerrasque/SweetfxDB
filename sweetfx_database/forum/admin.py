from . import models as M
from django.contrib import admin
from reversion import admin as reversion

class ForumThread(reversion.VersionAdmin):
    list_display = ["title", "creator", "posts"]
    search_fields = ["title", "creator__username"]
    raw_id_fields = ["creator", "last_post"]
    date_hierarchy = "created"
    list_filter = ["state"]

def mark_as_spam(modeladmin, request, queryset):
    for post in queryset:
        post.update_state(2)

def mark_as_verified(modeladmin, request, queryset):
    for post in queryset:
        post.update_state(1)

class ForumPost(reversion.VersionAdmin):
    list_display = ["creator", "thread","text_short", "created", "state"]
    list_editable = ["state"]
    search_fields = ["text", "creator__username"]
    raw_id_fields = ["creator", "thread"]
    date_hierarchy = "created"
    list_filter = ["state"]
    actions = [mark_as_spam, mark_as_verified]

admin.site.register(M.Forum)
admin.site.register(M.ForumThread, ForumThread)
admin.site.register(M.ForumPost, ForumPost)