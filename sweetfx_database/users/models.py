from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from sweetfx_database.gamedb.models import RenderMixin, Preset

from django.urls import reverse

# Create your models here.

class Alert(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-id']

class Theme(models.Model):
    default = models.BooleanField(default=False)
    title = models.CharField(max_length=100)
    css = models.CharField(blank=True, max_length=255, help_text="CSS url for the theme", verbose_name="CSS url")

    def __unicode__(self):
        return self.title

class PresetFavorite(models.Model):
    preset = models.ForeignKey("gamedb.Preset", related_name="favorites", on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name="favorites", on_delete=models.CASCADE)
    added = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ("preset","user")

class UserProfile(RenderMixin, models.Model):
    template = '<a href="{{ object.get_absolute_url }}">{{ object.user }}</a>'
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    alerts = models.BooleanField(default=False)
    description = models.TextField(blank=True)
    css = models.CharField(blank=True, max_length=255, help_text="Custom CSS url to use on the site", verbose_name="CSS url")
    theme = models.ForeignKey(Theme, blank=True, null=True, on_delete=models.CASCADE)
    
    def get_fav_presets(self):
        return Preset.objects.filter(favorites__user=self.user)
    
    def add_alert(self, message):
        Alert.objects.create(owner = self.user, text=message)

    def get_absolute_url(self):
        return reverse('user-detail', args=[str(self.user.username)])

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

def set_unread_alert(sender, instance, created, **kwargs):
    if created:
        profile = instance.owner.get_profile()
        profile.alerts = True
        profile.save()

post_save.connect(create_user_profile, sender=User)
post_save.connect(set_unread_alert, sender=Alert)
