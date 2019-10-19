from sweetfx_database.gamedb import models as gamedb
from sweetfx_database.users import models as userdb
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from . import forms

from django.shortcuts import redirect

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator


class LoginReq(object):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginReq, self).dispatch(*args, **kwargs)

class AboutView(TemplateView):
    template_name = "about.html"

class UserDetail(DetailView):
    model = gamedb.User
    slug_field = "username"
    context_object_name = "object"
    template_name = "users/user_detail.html"


class PresetFavorites(LoginReq, ListView):
    template_name = "users/favorites.html"
    
    def get_queryset(self):
        return userdb.PresetFavorite.objects.filter(user=self.request.user)

class UserAlerts(LoginReq, ListView):
    template_name = "users/alerts.html"
    
    def get_queryset(self):
        p=self.request.user.userprofile
        p.alerts = False
        p.save()
        return userdb.Alert.objects.filter(owner=self.request.user)

class UserProfile(LoginReq, UpdateView):
    template_name="users/userprofile.html"
    form_class = forms.ProfileForm

    def get_object(self):
        return self.request.user.userprofile

@login_required
def remove_user(request):
    uid = request.POST.get("userid")
    if request.method=="POST" and request.user.is_superuser and uid:
        user = userdb.User.objects.get(id=uid)
        user.delete()
    return redirect("/")


@login_required
def remove_preset_from_favorite(request):
    preset_id = int(request.POST.get("preset"))
    preset = gamedb.Preset.objects.get(id=preset_id)
    userdb.PresetFavorite.objects.get(preset=preset, user=request.user).delete()
    return redirect("user-favs")
    
@login_required
def add_preset_to_favorite(request):
    preset_id = int(request.POST.get("preset"))
    preset = gamedb.Preset.objects.get(id=preset_id)
    userdb.PresetFavorite.objects.create(preset=preset, user=request.user)
    return redirect(preset)
