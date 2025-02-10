from django.conf.urls import include, url
from django.views.generic import RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
from sweetfx_database.gamedb.cloudflare_turnstile import RegistrationForm
from django_registration.backends.one_step.views import RegistrationView

urlpatterns = [
    # Examples:
    url(r'^$', RedirectView.as_view(url="/games/"), name='home'),
    url(r'^games/', include('sweetfx_database.gamedb.urls')),
    url(r'^silly/', include('sweetfx_database.silly.urls')),
    url(r'^users/', include('sweetfx_database.users.urls')),
    url(r'^forum/', include('sweetfx_database.forum.urls')),
    url(r'^downloads/', include('sweetfx_database.downloads.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', admin.site.urls),
    url(
        'accounts/register/$',
        RegistrationView.as_view(
            form_class=RegistrationForm
        ),
        name='django_registration_register'
    ),
    url(r'^accounts/', include('django_registration.backends.one_step.urls')),
    url(r'^accounts/', include('django.contrib.auth.urls')),
    #(r'^account/', include('django_authopenid.urls')),
    url(r'^api/', include('sweetfx_database.api.urls')),
]
