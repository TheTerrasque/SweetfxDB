from django.conf.urls import url
from sweetfx_database.forum import views
from django.contrib.auth.decorators import login_required as li

urlpatterns = [
    url(r'^$', views.ForumList.as_view(), name='forum-main'),
    url(r'^(?P<slug>\w+)/$', views.Forum.as_view(), name='forum-view'),
    url(r'^(?P<slug>\w+)/new/$', views.NewForumThread.as_view(), name='forum-new-thread'),
    url(r'^(?P<forumslug>\w+)/(?P<pk>\w+)/$', views.ForumThread.as_view(), name='forum-thread'),
    url(r'^post/(?P<pk>\w+)/edit/$', views.EditPost.as_view(), name='forum-post-edit'),
    url(r'^(?P<forumslug>\w+)/(?P<pk>\w+)/POST/$', views.NewForumPost.as_view(), name='forum-thread-post'),
]
