import models as gamedb
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
# Create your views here.
from django.views.generic import ListView, DetailView, CreateView, UpdateView, TemplateView
import forms
from datetime import datetime
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.contenttypes.models import ContentType
from django.utils import simplejson

from django.http import Http404

from django.utils.html import escape

class LoginReq(object):

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginReq, self).dispatch(*args, **kwargs)

class GQsMixin(object):
    queryset = gamedb.Game.active.all()

class PaginateMixin(object):
    paginate_by = 25

class GameList(PaginateMixin, GQsMixin, ListView):
    pass

class GameDetails(GQsMixin, DetailView):
    pass

class AddPreset(LoginReq, CreateView):
    form_class = forms.PresetForm
    template_name = "gamedb/add_preset.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        mypk = self.kwargs.get("pk")
        game = gamedb.Game.objects.get(id=mypk)
        self.object.game = game
        self.object.creator = self.request.user
        return super(AddPreset, self).form_valid(form)

def search(request):
    query = request.REQUEST.get("query")
    data = {}
    if query:
        games = gamedb.Game.active.filter(title__icontains=query)[:5]
        r = {}
        r["Games"] = [{"title": x.title, "url": x.get_absolute_url()} for x in games]
        data = simplejson.dumps(r)
    return HttpResponse(data, mimetype="text/json")
    

class AddGame(LoginReq, CreateView):
    form_class = forms.GameForm
    template_name = "gamedb/add_game.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.creator = self.request.user
        return super(AddGame, self).form_valid(form)

class AddScreenshot(LoginReq, CreateView):
    form_class = forms.PresetScreenshotForm
    template_name = "gamedb/add_screenshot.html"

    def form_valid(self, form):
        self.object = form.save(commit=False)
        mypk = self.kwargs.get("pk")
        preset = gamedb.Preset.objects.get(id=mypk)

        if preset.creator != self.request.user:
            return

        self.object.creator = self.request.user
        self.object.preset = preset
        return super(AddScreenshot, self).form_valid(form)

class ShaderList(ListView):
    queryset = gamedb.Shader.objects.all()

class ShaderDetails(DetailView):
    queryset = gamedb.Shader.objects.all()

class PresetDetails(DetailView):
    queryset = gamedb.Preset.active.all()

def download_preset(request, pk):
    try:
        r = gamedb.Preset.active.get(id=pk)
    except gamedb.Preset.DoesNotExist:
        raise Http404
    
    r.downloads +=1
    r.save()
    response = HttpResponse(mimetype='text/plain')
    response['Content-Disposition'] = 'attachment; filename="SweetFX_Settings_%s_%s.txt"' % (r.game.title.encode("utf8"), r.title.encode("utf8"))
    response.write(r.settings_text)
    return response

class ScreenshotDetails(DetailView):
    queryset = gamedb.PresetScreenshot.active.all()

class LatestPresets(PaginateMixin, ListView):
    queryset = gamedb.Preset.active.all().order_by("-id")

class PopularPresets(PaginateMixin, ListView):
    queryset = gamedb.Preset.active.all().order_by("-downloads", "title")
    template_name = "gamedb/preset_list_popular.html"

class ScreenshotFull(DetailView):
    template_name = "gamedb/presetscreenshot_full.html"
    queryset = gamedb.PresetScreenshot.active.all()

class EditPreset(LoginReq, UpdateView):
    template_name="gamedb/generic_form.html"
    form_class = forms.PresetForm

    def form_valid(self, form):
        form.instance.updated = datetime.now()
        for fav in form.instance.favorites.all():
            fav.user.get_profile().add_alert(u"Preset %s was updated" % form.instance.render())
        return super(EditPreset, self).form_valid(form)

    def get_queryset(self):
        return gamedb.Preset.objects.filter(creator=self.request.user)

class EditScreenshot(LoginReq, UpdateView):
    template_name="gamedb/generic_form.html"
    form_class = forms.PresetScreenshotForm

    def get_queryset(self):
        return gamedb.PresetScreenshot.objects.filter(creator=self.request.user)

class EditGame(LoginReq, UpdateView):
    template_name="gamedb/generic_form.html"
    form_class = forms.GameForm

    def get_queryset(self):
        return gamedb.Game.objects.filter(creator=self.request.user)

@login_required
def save_comment(request):
    data = request.POST
    cname = data.get("cname").replace(" ", "")
    comment = data.get("comment").strip()
    cid = data.get("cid")
    if comment:
        ctype = ContentType.objects.get(model=cname)
        obj = ctype.get_object_for_this_type(id=cid)
        objname = escape(unicode(obj))
        c = gamedb.UserComment(comment=comment, creator=request.user)
        c.content_object = obj
        c.save()
        
        if request.user != obj.creator:
            msg = "You have a new comment on : <a href='%s'>%s</a>" % (obj.get_absolute_url(), objname)
            obj.creator.get_profile().add_alert(msg)
        
        return HttpResponseRedirect(obj.get_absolute_url() + "#comments")
    return HttpResponseRedirect("/")

class ServeTemplate(TemplateView):
    def get_template_names(self):
        t = self.kwargs["template"]
        return "gamedb/static/%s.html" % t
