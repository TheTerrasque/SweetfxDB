# Django settings for sweetfx_database project.
import os
import django

# calculated paths for django and the site
# used as starting points for various other paths
DJANGO_ROOT = os.path.dirname(os.path.realpath(django.__file__))
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
SITE_ROOT = os.path.dirname(SITE_ROOT)
def pj(*path):
    return os.path.join(SITE_ROOT, *path)

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ALLOWED_HOSTS = ["*"]

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': pj('data/data.sqlite3'),                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Europe/Oslo'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = False

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = pj("media")

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = pj('static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", 'j%zh%perbg4)o))jb*jcx66t6zi1$l_gcohs&amp;l0csk533t05s8')

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE = (
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'reversion.middleware.RevisionMiddleware',
    #'django_authopenid.middleware.OpenIDMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'sweetfx_database.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'sweetfx_database.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

#CSSURL = "/static/css/style.css"
CSSURL = "/static/css/pcmr/pcmr.css"

INTERNAL_IPS = ["127.0.0.1"]

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'sweetfx_database.gamedb',
    "django.contrib.humanize",
    "django_registration",
    "reversion",
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    "sweetfx_database.silly",
    "sweetfx_database.users",
    "sweetfx_database.forum",
    "sweetfx_database.downloads",
    #'django_authopenid',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    "sweetfx_database.api",
    "rest_framework"
)

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
)

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                "sweetfx_database.users.context_processors.set_style",
                "django.template.context_processors.media",
            ],
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

TEMPLATE_CONTEXT_PROCESSORS = ("django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    'django.core.context_processors.request',
    "django.core.context_processors.tz",
    "django.contrib.messages.context_processors.messages",
    "sweetfx_database.users.context_processors.set_style",
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake'
    }
}

ACCOUNT_ACTIVATION_DAYS=7

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/games/'
LOGOUT_REDIRECT_URL = "/games/"

AUTH_PROFILE_MODULE = 'users.UserProfile'

DATETIME_FORMAT="j M H:i T"

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    'PAGINATE_BY': 20,
    "URL_FIELD_NAME": "link",
    "PAGINATE_BY_PARAM": "page_size",
    "MAX_PAGINATE_BY": 200,      
}

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

#WSGI_APPLICATION = 'app.wsgi.application'

CLOUDFLARE_TURNSTILE_SECRET = os.getenv("CLOUDFLARE_TURNSTILE_SECRET")
CLOUDFLARE_TURNSTILE_SITEKEY = os.getenv("CLOUDFLARE_TURNSTILE_SITEKEY")

OPENAI_BASE_URL = os.getenv("SFX_OPENAI_BASE_URL", "")
OPENAI_KEY = os.getenv("SFX_OPENAI_KEY", "")
OPENAI_MODEL = os.getenv("SFX_OPENAI_MODEL", "")
FORUM_RULES = """
Classify the following content as wanted or not wanted on the forum. Give a reason for your answer.

The forum is for a software called sweetfx and it's successor, reshade. 
Presets for reshade or sweetfx are sometimes called mods by the users, and are used to enhance the graphics of pc games.

Allowed:
- Discussions on pc games and different presets for sweetfx, reshade or related programs.
- Asking about help with creating presets, sharing presets, or asking someone to create a preset for a game.
- Asking for or talking about a preset for a game.
- Asking for or talking about a mod or mods for a game.
- Talking about or discussing specific pc games or hardware, as long as there's no strange links.
- Asking if there exist a preset or mod for a game, and where to find it.
- Content discussing the site itself, talk between users, and friendly chat and banter
- Asking for help with a game, or how to use sweetfx or reshade in a game.
- Content with links to the official site, or to the official forum.
- Content with links to the official documentation, or to the official download page.
- Content discussing the use of reshade or sweetfx in games, legality, and how to install it.
- Technical support and help with sweetfx and reshade, and specific games. 
  - This includes asking about dll's like dxgi.dll, d3d9.dll, d3d11.dll, opengl32.dll and so on, as they're used as loaders / injectors for sweetfx and reshade.
- Content talking about the site, forum and issues, and asking for help.
- Content discussing different effects and shaders, and how to use them in games.
- Discussions about pc monitors and graphics cards.
- Thanking someone for help, or for creating a preset or mod.

Not allowed:
- Anything promoting or referring to external services not related to the site, reshade or sweetfx.
- Random bullshit, like list of programs or user experiences with casinos.
- Talk about non-computer games, like for example football, or other sports.
- Talk about politics, religion, or other controversial topics.
- Talk about writing assitance, essay writing or other academic help.
- Content with many unexplained links, or referring to gambling, casinos, cryptocurrency or advertising, together with any other content that is not related to the forum.
- Non-english Content are not allowed unless clearly mentioning pc games, sweetfx or reshade.
- Cracked software, or any other illegal content.
- Long posts with no clear content, or posts with no clear meaning.
- Long posts with clear focus on something external to the forum.
- Linking to external sites with no clear purpose, or linking to sites that are not related to the forum.
- Otherwise helpful generic content that has a link suddenly appearing with no context in the middle of it.

If unsure or the content is not clear, mark it as maybe and give a reason for your answer. 
Small, ambiguous posts should be given the benefit of the doubt, unless there's suspicious links.
"""

DEFAULT_THREAD_PROMPT= """
{{RULES}}

-------------------
Forum: {{thread.forum}}
User: {{creator}}
Thread title: {{post.thread}}
First post content: {{text}}
-------------------

Is this thread wanted on the forum? 
"""

DEFAULT_POST_PROMPT = """{{RULES}}

Post:
-------------------
Forum: {{post.thread.forum}}
Thread: {{post.thread}}
User: {{post.creator}}
Text: {{post.text}}
-------------------
Is this post wanted on the forum?
"""

try:
    from .settings_local import *
except ImportError:
    print("No local settings found")
    pass
