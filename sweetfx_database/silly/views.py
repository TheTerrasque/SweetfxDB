# Create your views here.
from tools import namegen

from django.views.generic import TemplateView
from django.http import HttpResponse
from django.utils import simplejson as json
from django.views.decorators.cache import cache_control, never_cache

class GameNames(TemplateView):
    template_name = "silly/silly.html"

    def get_context_data(self, **kwargs):
        context = super(GameNames, self).get_context_data(**kwargs)
        context['total_names'] = namegen.count_gamenames()
        return context

@never_cache
def get_gamenames(request):
    num = int(request.GET.get("num", 1))
    r = []
    for x in range(num):
        r.append(namegen.make_gamename())
    content = json.dumps(r)
    return HttpResponse(content, content_type='application/json')

class ServeTemplate(TemplateView):
    def get_template_names(self):
        t = self.kwargs["template"]
        return "silly/t/%s.html" % t
