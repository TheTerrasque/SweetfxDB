from django.db import models
from django.contrib.auth.models import User
from django.template import Template, Context
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.fields import GenericRelation

from django.utils.translation import ugettext_lazy as _

from django.urls import reverse

from django.core.cache import cache

from django.db.models.signals import post_save
from django.dispatch import receiver
# Create your models here.

from . import imageLogic
import os

#Not in use any more
SWEETFX_VERSION = (
#    (7, "1.6"),
    (8, "GemFX"),
    (6, "eFX"),
    (5, "SweetFX 1.5"),
    (4, "SweetFX 1.4"),
    (3, "SweetFX 1.3"),
    (2, "SweetFX 1.2"),
    (1, "SweetFX 1.1"),
    (0, "SweetFX 1.0"),
)

class ActiveManager(models.Manager):
    def get_queryset(self):
        return super(ActiveManager, self).get_queryset().filter(visible=True)
    

class RenderMixin(object):
    template = '<a href="{{ object.get_absolute_url }}">{{ object }}</a>'

    def render(self):
        return render_template(self.template, {"object": self})

class UserComment(models.Model):
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    added = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True, blank=True)

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(db_index=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return u"%s comment by %s" % (self.content_type, self.creator)

    def get_text_start(self):
        return self.comment[:50]

    class Meta:
        ordering = ["-id"]

class Game(RenderMixin, models.Model):
    title = models.CharField(db_index=True, max_length=50, help_text= _("The name of the game"))
    url = models.URLField(blank=True, help_text= _("Home page for the game"))
    exename = models.CharField(max_length=20, blank = True, help_text= _("Name of the executable for this game"))
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    added = models.DateField(auto_now_add=True)
    visible = models.BooleanField(default=True, blank=True, db_index=True)
    sweetfx_notes = models.TextField(blank=True, help_text= _("Any general SweetFX notes about this game"))

    preset_count = models.IntegerField(default=0)

    comments = GenericRelation(UserComment)

    active = ActiveManager()
    objects = models.Manager()

    def update_preset_count(self):
        self.preset_count = self.get_presets().count()

    def get_comments(self):
        return self.comments.filter(visible=True)

    def get_presets(self):
        return self.preset_set.filter(visible=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["title"]

    def get_absolute_url(self):
        return reverse('g-game-detail', args=[str(self.id)])

class Shader(RenderMixin, models.Model):
    
    name = models.CharField(max_length=40)
    url = models.URLField(blank=True)
    description = models.TextField(blank=True)
    download = models.ForeignKey("downloads.DownloadFile", null=True, blank = True, on_delete=models.CASCADE)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ["name"]

    def get_absolute_url(self):
        return reverse('g-shader-detail', args=[str(self.id)])
    
class Preset(RenderMixin, models.Model):
    title = models.CharField(max_length=40, help_text= _("The name of the preset"))
    added = models.DateField(auto_now_add=True)
    updated = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True)
    settings_text = models.TextField(help_text= _("The actual preset settings"))
    creator = models.ForeignKey(User, on_delete=models.CASCADE)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)

    visible = models.BooleanField(db_index=True, default=True, blank=True, help_text="Display the preset on the game page")
    active = ActiveManager()
    objects = models.Manager()

    #sweetfx_version = models.IntegerField(choices=SWEETFX_VERSION, help_text= _("The SweetFX version the config is for"))
    shader = models.ForeignKey(Shader, null=True, on_delete=models.CASCADE)

    downloads = models.IntegerField(default=0, db_index=True)
    screenshot_count = models.IntegerField(default=0)
    comments = GenericRelation(UserComment)
    
    def update_screenshot_count(self):
        self.screenshot_count = self.get_screenshots().count()
    
    def get_comments(self):
        return self.comments.filter(visible=True)
        
    def get_screenshots(self):
        return self.presetscreenshot_set.filter(visible=True)

    def is_active(self, user=None):
        return self.visible

    def __str__(self):
        return self.title

    class Meta:
        ordering = ["title", "id"]

    def get_absolute_url(self):
        return reverse('g-preset-detail', args=[str(self.id)])

class PresetScreenshot(RenderMixin, models.Model):
    template = """<a href="{{ object.get_absolute_url }}">
            <div class="imagethumb">
                <img src="{{ object.small_thumb.url }}"/>
                <div class="imageinfo">
                    <div class="imagedetails">
                        <div class="imgsize">{{ object.image_width }}x{{ object.image_height }}</div>
                        <div class="added">SweetFX: {{ object.get_type }}</div>
                    </div>
                </div>
            </div>
        </a>"""

    preset = models.ForeignKey(Preset, on_delete=models.CASCADE)
    image = models.ImageField(verbose_name = _("SweetFX image"), upload_to="presetscreenshots/%Y/%m/%d/", height_field="image_height", width_field="image_width", help_text= _("The main image, the screenshot itself"))
    image_height = models.IntegerField(default=0)
    image_width = models.IntegerField(default=0)

    comparison_image = models.ImageField(upload_to="presetscreenshotscompare/%Y/%m/%d/", blank=True, null = True, help_text= _("Optional comparison image, where SweetFX is OFF"))

    SFX_STATES = (
        (2, _("Split screen")),
        (3, _("Enabled")),
    )

    sweetfx_state = models.IntegerField(choices=SFX_STATES, help_text= _("What state SweetFX is in the main image"))

    description = models.TextField(blank=True)

    visible = models.BooleanField(db_index=True, default=True, blank=True, help_text="Display the screenshot on the preset page")
    active = ActiveManager()
    objects = models.Manager()

    medium_thumb = models.ImageField(upload_to="medthumb/%Y/%m/%d/")

    medium_thumb_compared = models.ImageField(upload_to="medthumb/%Y/%m/%d/", blank = True, null = True)

    small_thumb = models.ImageField(upload_to="smallthumb/%Y/%m/%d/")
    created = models.DateField(auto_now_add=True)
    creator = models.ForeignKey(User, on_delete=models.CASCADE)

    optimized = models.BooleanField(default=False)

    def optimize(self):
        if self.image.path.lower().endswith(".png"):
            imageLogic.optimize_png(self.image.path)
            self.optimized = True
            self.save()

    def compress_main_image(self):
        path = self.image.path
        ci = imageLogic.CompressImage(path)
        if ci.should_compress():
            self.image.save(*ci.save_image())
            os.unlink(path)
            #os.rename(path, path + ".%s.old" % self.id)
    
    def compress_comparison_image(self):
        if self.comparison_image:
            path = self.comparison_image.path
            ci = imageLogic.CompressImage(path)
            if ci.should_compress():
                self.comparison_image.save(*ci.save_image())
                os.unlink(path)
                #os.rename(path, path + ".%s.old" % self.id)
    
    def make_thumbs(self):
        name, data = imageLogic.resize_image(self.image.path, (1000, 700), 80)
        self.medium_thumb.save(name, data)
        name, data = imageLogic.resize_image(self.image.path, (300, 200))
        self.small_thumb.save(name, data)
        if self.comparison_image:
            name, data = imageLogic.resize_image(self.comparison_image.path, (1000, 700), 80)
            self.medium_thumb_compared.save(name, data)

        self.compress_main_image()
        self.compress_comparison_image()

    comments = GenericRelation(UserComment)
    def get_comments(self):
        return self.comments.filter(visible=True)
        
    def __str__(self):
        return u"Screenshot - %s (%s)" % (self.preset, self.preset.game)

    class Meta:
        ordering = ["-id"]

    def get_type(self):
        if self.comparison_image:
            return "Comparison"
        return self.get_sweetfx_state_display()

    def get_absolute_url(self):
        return reverse('g-screenshot-detail', args=[str(self.id)])

def render_template(templatestr, contextdict):
    t = Template(templatestr)
    c = Context(contextdict)
    return t.render(c)

@receiver(post_save, sender=Preset)
def update_game_preset_number(sender, **kwargs):
    instance = kwargs["instance"]
    g = instance.game
    g.update_preset_count()
    g.save()

@receiver(post_save, sender=PresetScreenshot)
def my_handler(sender, **kwargs):
    instance = kwargs["instance"]
    key = "psc%s" % instance.id
    mkey = "prc%s" % instance.id
    
    p = instance.preset
    p.update_screenshot_count()
    p.save()
    
    if instance.image.name != cache.get(key) or (instance.comparison_image and (instance.comparison_image.name != cache.get(mkey))):
        cache.set(key, instance.image.name)
        if instance.comparison_image:
            cache.set(mkey, instance.comparison_image.name)
        instance.make_thumbs()
