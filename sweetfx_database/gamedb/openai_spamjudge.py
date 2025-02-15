import openai
import json
import jinja2
from django.conf import settings
from sweetfx_database.forum import models as fm
from . import models as gm
import re

BASE_URL = getattr(settings, "OPENAI_BASE_URL", None)
KEY = getattr(settings, "OPENAI_KEY", None)
MODEL = getattr(settings, "OPENAI_MODEL", None)
ARGS = getattr(settings, "OPENAI_ARGS", {"temperature":0.1, "timeout": 60})

RULES = getattr(settings, "FORUM_RULES", None)
POST_PROMPT = getattr(settings, "DEFAULT_POST_PROMPT", None)
THREAD_PROMPT = getattr(settings, "DEFAULT_THREAD_PROMPT", None)

active = False

RESPONSE_FORMAT = """ Give the answer in json: { "wanted": "yes|no|maybe", "reason":"<reason>"}"""

if KEY and MODEL and RULES and POST_PROMPT and THREAD_PROMPT:
    client = openai.OpenAI(api_key=KEY, base_url=BASE_URL)
    post_template = jinja2.Template(POST_PROMPT + RESPONSE_FORMAT)
    thread_template = jinja2.Template(THREAD_PROMPT + RESPONSE_FORMAT)
    active = True

def remove_user_posting_permissions(user: fm.userdb.User):
    forum_permission = fm.Permission.objects.get(codename="post_on_forum")
    gamedb_permission = fm.Permission.objects.get(codename="post_on_games")
    user.user_permissions.remove(forum_permission)
    user.user_permissions.remove(gamedb_permission)


def call_llm_and_get_response(prompt):
    r = client.chat.completions.create(model=MODEL, messages=[{"role":"user", "content":prompt}], **ARGS)
    result = r.choices[0].message.content.strip()
    # Clean markdown
    result = re.sub(r"```[a-zA-Z]*", "", result).strip("`\n")
    j = json.loads(result)
    j["rating"] = {"yes": 1, "no": 2, "maybe": 3}[j["wanted"]]
    return j

def judge_post(post: fm.ForumPost):
    if not active: return

    prompt = post_template.render(RULES=RULES, post=post)
    try:
        response = call_llm_and_get_response(prompt)
        post.update_state(response["rating"], response["reason"])
    except Exception as e:
        post.update_state(4, str(e))
    if post.state in fm.POST_SPAM_STATES:
        num_spams = fm.ForumPost.objects.filter(state__in=fm.POST_SPAM_STATES).count()
        num_nonspams = fm.ForumPost.objects.filter(state__in=fm.POSTS_VISIBLE_STATES).count()
        if num_spams > num_nonspams:
            remove_user_posting_permissions(post.creator)
