from models import Theme

DEFAULT = "/static/css/style.css"

def set_style(request):
    r = { "CSSURL" : DEFAULT }
    q = Theme.objects.filter(default=True)
    if q:
        r = { "CSSURL" : q[0].css }
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        if profile.css.strip():
            r = { "CSSURL" : profile.css.strip()}
        elif profile.theme:
            r = { "CSSURL" : profile.theme.css}
    return r
