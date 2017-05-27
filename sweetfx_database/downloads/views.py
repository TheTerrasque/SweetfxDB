# Create your views here.
from sweetfx_database.downloads import models
from django.views.generic import TemplateView, ListView, DetailView, UpdateView

class Downloads(ListView):
    model = models.DownloadCategory
