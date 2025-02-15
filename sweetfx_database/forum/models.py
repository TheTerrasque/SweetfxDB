from django.db import models
from sweetfx_database.users import models as userdb
from sweetfx_database.gamedb.models import RenderMixin
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
# Create your models here.
from django.urls import reverse

from django_registration.signals import user_registered
from django.contrib.auth.models import Permission

POSTS_VISIBLE_STATES = [0, 1, 3, 4]
POST_SPAM_STATES = [2]

class Forum(RenderMixin, models.Model):
    title = models.CharField(max_length=50)
    description = models.CharField(max_length=100)
    updated = models.DateTimeField(auto_now_add=True, db_index=True)
    sorting = models.PositiveIntegerField(default=100, db_index=True)
    parent = models.ForeignKey('self', blank=True, null=True, on_delete=models.CASCADE)
    threads = models.PositiveIntegerField(default=0)
    slug = models.SlugField()
    last_thread = models.ForeignKey("ForumThread", null=True, blank=True, related_name="forum2", on_delete=models.SET_NULL)
    
    def __str__(self):
        return u"%s" % self.title

    class Meta:
        ordering = ['-sorting']
        permissions = [
            ("post_on_forum", "Can post on forum"),
        ]

    def update_state(self):
        #forum.updated = datetime.datetime.now()
        #     forum.threads = forum.forumthread_set.count()
        #     forum.last_thread = instance
        threads = self.get_threads()
        self.threads = threads.count()
        self.last_thread = threads.first()
        if self.last_thread:
            self.updated = self.last_thread.updated
        self.save()

    def get_threads(self):
        return self.forumthread_set.filter(state=1)

    def get_absolute_url(self):
        return reverse('forum-view', args=[self.slug])

class ForumThreadManager(models.Manager):
    def latest_threads(self):
        return self.filter(state=1)

class ForumThread(RenderMixin, models.Model):
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    creator = models.ForeignKey(userdb.User, on_delete=models.CASCADE)
    title = models.CharField(max_length=50)
    posts = models.PositiveIntegerField(default=0)
    sorting = models.PositiveIntegerField(default=100, db_index=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now_add=True, db_index=True)
    last_post = models.ForeignKey("ForumPost", null=True, blank=True, on_delete=models.SET_NULL)
    state = models.IntegerField(choices=[
        (0, "Hidden"),
        (1, "Visible")
    ], default=1)

    objects = ForumThreadManager()

    def __str__(self):
        return u"%s" % self.title
        
    class Meta:
        ordering = ['-sorting', "-updated"]
    
    def get_posts(self):
        return self.forumpost_set.filter(state__in = POSTS_VISIBLE_STATES)

    def update_state(self):
        if self.get_posts().exists():
            self.state = 1
            self.posts = self.get_posts().count()
            self.last_post = self.get_posts().last()
            self.updated = self.last_post.created
        else:
            self.state = 0
        self.save()
        self.forum.update_state()

    def get_absolute_url(self):
        return reverse('forum-thread', args=[self.forum.slug, str(self.id)])
        
class ForumPost(models.Model):
    thread = models.ForeignKey(ForumThread, on_delete=models.CASCADE)
    creator = models.ForeignKey(userdb.User, on_delete=models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(blank=True, null=True)
    ip = models.CharField(max_length=200, blank=True)
    
    state_reason = models.TextField(blank=True, default="")
    state = models.IntegerField(choices=[
        (0, "Unchecked"),
        (1, "Visible"),
        (2, "Spam"),
        (3, "Unsure"),
        (4, "Error"),
    ], default=0)

    def text_short(self):
        return self.text[:100]

    def update_state(self, newstate=None, reason=None):
        if newstate != None:
            self.state = newstate
            if reason:
                self.state_reason = reason
            self.save()
        self.thread.update_state()

    def is_edited(self):
        return self.updated and self.created.toordinal() != self.updated.toordinal()
    
    def get_absolute_url(self):
        return reverse('forum-thread', args=[self.thread.forum.slug, str(self.thread.id)])
    
    def __str__(self):
        return u"%s [%s]" % (self.thread.title, self.id)

    class Meta:
        ordering = ['created']

@receiver(post_save, sender=ForumPost)
def handle_new_forum_post(sender, **kwargs):
    instance = kwargs["instance"]
    instance.update_state()
    # if kwargs["created"]:
    #     thread = instance.thread
    #     thread.last_post = instance
    #     thread.updated = datetime.datetime.now()
    #     thread.posts = thread.get_posts().count()
    #     thread.save()
    
# @receiver(post_save, sender=ForumThread)
# def handle_forum_thread_update(sender, **kwargs):
#     instance = kwargs["instance"]
#     forum = instance.forum
#     forum.updated = datetime.datetime.now()
#     forum.threads = forum.forumthread_set.count()
#     forum.last_thread = instance
#     forum.save()

@receiver(post_delete, sender=ForumPost)
def handle_delete_forum_post(sender, instance, **kwargs):
    instance.thread.update_state()

@receiver(user_registered)
def add_permission(sender, user, request, **kwargs):
    permission_object = Permission.objects.get(codename="post_on_forum")
    user.user_permissions.add(permission_object)