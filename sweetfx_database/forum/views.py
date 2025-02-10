from datetime import timedelta, timezone
from http.client import HTTPResponse
from django.contrib.auth.models import Permission
from . import models as forumdb
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
from sweetfx_database.gamedb.views import LoginReq, PaginateMixin
from django.contrib.auth.mixins import PermissionRequiredMixin
from . import forms
from django.utils.html import escape


class PermissionReq(PermissionRequiredMixin):
    permission_required = "forum.post_on_forum"
    permission_denied_message = "Posting is disabled for new users. Contact Terrasque on Discord to enable posting for your account"

class ForumList(PaginateMixin, ListView):
    template_name = "forum/index.html"
    queryset = forumdb.Forum.objects.all()

class Forum(DetailView):
    template_name = "forum/forum.html"
    context_object_name = 'forum'
    queryset = forumdb.Forum.objects.all().select_related("last_thread")

class ForumThread(DetailView):
    template_name = "forum/forum_thread.html"
    context_object_name = 'thread'
    queryset = forumdb.ForumThread.objects.all().select_related()

class EditPost(LoginReq, UpdateView):
    form_class = forms.NewPostForm
    model = forumdb.ForumPost
    template_name = "forum/editpost.html"

    def get_queryset(self):
        base_qs = super(EditPost, self).get_queryset()
        return base_qs.filter(creator=self.request.user)

class NewForumThread(PermissionReq, CreateView):
    form_class = forms.NewThreadForm
    template_name = "forum/new_thread.html"
    
    def render_to_response(self, context, **kwargs):
        context["forum"] = self.get_forum()
        return super(NewForumThread, self).render_to_response(context, **kwargs)
    
    def get_forum(self):
        forum_slug = self.kwargs['slug']
        forum = forumdb.Forum.objects.get(slug=forum_slug)
        return forum
    
    def form_valid(self, form):
        forum = self.get_forum()
        
        post_text = form.cleaned_data['text']
        
        self.object = form.save(commit=False)
        self.object.forum = forum
        self.object.creator = self.request.user
        
        x = super(NewForumThread, self).form_valid(form)
        
        new_post = forumdb.ForumPost.objects.create(thread=self.object, creator=self.request.user, text=post_text)
        
        return x

class NewForumPost(PermissionReq, CreateView):
    form_class = forms.NewPostForm
    template_name = "forum/new_thread.html"
    
    def form_valid(self, form):
        if self.request.user.date_joined > timezone.now() - timedelta(minutes=15):
            permission_object = Permission.objects.get(codename="post_on_forum")
            self.request.user.user_permissions.remove(permission_object)
            return HTTPResponse("A problem occurred. Please contact Terrasque on Discord to fix.")
        
        pk = self.kwargs['pk']
        thread = forumdb.ForumThread.objects.get(id=pk)
        
        if self.request.user != thread.creator:
            msg = "Someone created a new post on thread : <a href='%s'>%s</a>" % (thread.get_absolute_url(), escape(thread))
            thread.creator.userprofile.add_alert(msg)
        
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        self.object.thread = thread
        self.object.ip = self.request.META['REMOTE_ADDR']
        return super(NewForumPost, self).form_valid(form)
