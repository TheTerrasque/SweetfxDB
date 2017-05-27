from django.contrib.syndication.views import Feed
import models as gamedb

class LatestPresetsFeed(Feed):
    title = "SweetFX Game Settings"
    link = "/games/"
    description = "Updates on new SweetFX game settings"

    def items(self):
        return gamedb.Preset.objects.order_by('-id')[:15]

    def item_title(self, item):
        return u"%s - %s" % (item.game.title, item.title)

    def item_description(self, item):
        return "[For %s - Added by %s] " % (item.shader, item.creator) + item.description
