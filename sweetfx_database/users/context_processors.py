from .models import Theme
from django.conf import settings

DEFAULT = settings.CSSURL or "/static/css/style.css"

def set_style(request):
    r = { "CSSURL" : DEFAULT }
    q = Theme.objects.filter(default=True)
    if q:
        r = { "CSSURL" : q[0].css }
    if request.user.is_authenticated:
        profile = request.user.userprofile
        if profile.css.strip():
            r = { "CSSURL" : profile.css.strip()}
        elif profile.theme:
            r = { "CSSURL" : profile.theme.css}
    return r
