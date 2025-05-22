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

RESPONSE_FORMAT = """ Give the answer in json: { "wanted": "yes|no|maybe", "reason":"<reason>"}"""

class OpenAISpamJudge:
    permissions_to_remove = ["post_on_forum", "post_on_games"]
    active = False
    def __init__(self, base_url = BASE_URL, key=KEY, model=MODEL, args=ARGS, rules=RULES, post_prompt=POST_PROMPT, thread_prompt = THREAD_PROMPT):
        if key and model and rules and post_prompt and thread_prompt:
            self.client = openai.OpenAI(api_key=key, base_url=base_url)
            self.post_template = jinja2.Template(post_prompt + RESPONSE_FORMAT)
            self.thread_template = jinja2.Template(thread_prompt + RESPONSE_FORMAT)
            self.rules = rules
            self.model = model
            self.args = args
            self.active = True

    def remove_user_posting_permissions(self, user: fm.userdb.User):
        for entry in self.permissions_to_remove:
            permission = fm.Permission.objects.get(codename=entry)
            user.user_permissions.remove(permission)

    def call_llm_and_get_response(self, prompt):
        r = self.client.chat.completions.create(model=self.model, messages=[{"role":"user", "content":prompt}], **self.args)
        result = r.choices[0].message.content.strip()
        # Clean markdown
        result = re.sub(r"```[a-zA-Z]*", "", result).strip("`\n")
        j = json.loads(result)
        j["rating"] = {"yes": 1, "no": 2, "maybe": 3}[j["wanted"]]
        return j

    def judge_post(self, post: fm.ForumPost):
        if not self.active: return -1

        prompt = self.post_template.render(RULES=self.rules, post=post)
        try:
            response = self.call_llm_and_get_response(prompt)
            post.update_state(response["rating"], response["reason"])
        except Exception as e:
            post.update_state(4, str(e))

        if post.state in fm.POST_SPAM_STATES:
            num_spams = fm.ForumPost.objects.filter(state__in=fm.POST_SPAM_STATES, creator=post.creator).count()
            num_nonspams = fm.ForumPost.objects.filter(state__in=fm.POSTS_VISIBLE_STATES, creator=post.creator).count()
            if num_spams > num_nonspams:
                self.remove_user_posting_permissions(post.creator)
                return 2
            return 1
        return 0
