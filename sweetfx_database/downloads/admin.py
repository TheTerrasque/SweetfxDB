import models as M
from django.contrib import admin
import reversion

class Category(reversion.VersionAdmin):
    list_display = ["name", "sortweight"]
    search_fields = ["name"]

class DlFile(reversion.VersionAdmin):
    list_display = ["name", "sortweight", "category"]
    search_fields = ["name"]


admin.site.register(M.DownloadCategory, Category)
admin.site.register(M.DownloadFile, DlFile)
