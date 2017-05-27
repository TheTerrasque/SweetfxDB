from django.db import models
from sweetfx_database.users import models as userdb
from sweetfx_database.gamedb.models import RenderMixin
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime
# Create your models here.

class Forum(RenderMixin, models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    updated = models.DateTimeField(auto_now_add=True, db_index=True)
    sorting = models.PositiveIntegerField(default=100, db_index=True)
    parent = models.ForeignKey('self', blank=True, null=True)
    threads = models.PositiveIntegerField(default=0)
    slug = models.SlugField()
    last_thread = models.ForeignKey("ForumThread", null=True, blank=True, related_name="forum2", on_delete=models.SET_NULL)
    
    def __unicode__(self):
        return u"%s" % self.title

    class Meta:
        ordering = ['-sorting']
        
    @models.permalink
    def get_absolute_url(self):
        return ('forum-view', [self.slug])
        
class ForumThread(RenderMixin, models.Model):
    forum = models.ForeignKey(Forum)
    creator = models.ForeignKey(userdb.User)
    title = models.CharField(max_length=50)
    posts = models.PositiveIntegerField(default=0)
    sorting = models.PositiveIntegerField(default=100, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True, db_index=True)
    last_post = models.ForeignKey("ForumPost", null=True, blank=True, on_delete=models.SET_NULL)
    
    def __unicode__(self):
        return u"%s" % self.title
        
    class Meta:
        ordering = ['-sorting', "-updated"]
    
    @models.permalink
    def get_absolute_url(self):
        return ('forum-thread', [self.forum.slug, str(self.id)])
        
class ForumPost(models.Model):
    thread = models.ForeignKey(ForumThread)
    creator = models.ForeignKey(userdb.User)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True, blank=True, null=True)
    ip = models.CharField(max_length=200, blank=True)
    
    def is_edited(self):
        return self.updated and self.created.toordinal() != self.updated.toordinal()
    
    @models.permalink
    def get_absolute_url(self):
        return ('forum-thread', [self.thread.forum.slug, str(self.thread.id)])
    
    def __unicode__(self):
        return u"%s [%s]" % (self.thread.title, self.id)

@receiver(post_save, sender=ForumPost)
def handle_new_forum_post(sender, **kwargs):
    instance = kwargs["instance"]
    if kwargs["created"]:
        thread = instance.thread
        thread.last_post = instance
        thread.updated = datetime.datetime.now()
        thread.posts = thread.forumpost_set.count()
        thread.save()
    
@receiver(post_save, sender=ForumThread)
def handle_forum_thread_update(sender, **kwargs):
    instance = kwargs["instance"]
    forum = instance.forum
    forum.updated = datetime.datetime.now()
    forum.threads = forum.forumthread_set.count()
    forum.last_thread = instance
    forum.save()
