import openai
import json
import jinja2
from django.conf import settings
from sweetfx_database.forum import models as fm
from . import models as gm

BASE_URL = getattr(settings, "OPENAI_BASE_URL", None)
KEY = getattr(settings, "OPENAI_KEY", None)
MODEL = getattr(settings, "OPENAI_MODEL", None)

RULES = getattr(settings, "FORUM_RULES", None)
POST_PROMPT = getattr(settings, "DEFAULT_POST_PROMPT", None)
THREAD_PROMPT = getattr(settings, "DEFAULT_THREAD_PROMPT", None)

active = False

if KEY and MODEL and RULES and POST_PROMPT and THREAD_PROMPT:
    client = openai.OpenAI(api_key=KEY, base_url=BASE_URL)
    post_template = jinja2.Template(POST_PROMPT)
    thread_template = jinja2.Template(THREAD_PROMPT)

    active = True

