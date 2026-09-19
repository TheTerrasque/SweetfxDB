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
ARGS = getattr(settings, "OPENAI_ARGS", {"temperature":0.1, "timeout": getattr(settings, "OPENAI_TIMEOUT", 60)})

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
            self.args = args if args is not None else ARGS
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

    def check_spam_permissions(self, post: fm.ForumPost):
        """Strip posting permissions if the user's spam posts outnumber
        their visible ones. Returns 2 if permissions were removed, 1 if
        the post is spam but permissions were kept, 0 otherwise.
        Works for spam verdicts from any tier (LLM or laya prefilter)."""
        if post.state not in fm.POST_SPAM_STATES:
            return 0
        num_spams = fm.ForumPost.objects.filter(state__in=fm.POST_SPAM_STATES, creator=post.creator).count()
        num_nonspams = fm.ForumPost.objects.filter(state__in=fm.POSTS_VISIBLE_STATES, creator=post.creator).count()
        if num_spams > num_nonspams:
            self.remove_user_posting_permissions(post.creator)
            return 2
        return 1

    def record_error(self, post: fm.ForumPost, error: Exception):
        """Store the error on the post (state 4) and count it. The post
        stays in state 4 and is picked up again by the next
        process_forum_spam run (every 9 minutes) until it accumulates
        MAX_ERROR_COUNT errors, so transient failures (rate limits,
        timeouts, malformed JSON) are retried every round while posts
        that keep failing are eventually left for a human."""
        post.error_count = (post.error_count or 0) + 1
        post.update_state(4, f"LLM judgment error: {error}")

    def judge_post(self, post: fm.ForumPost):
        if not self.active: return None

        prompt = self.post_template.render(RULES=self.rules, post=post)
        try:
            response = self.call_llm_and_get_response(prompt)
            newstate = response["rating"]
            reason = response["reason"]
            post.error_count = 0
            post.update_state(newstate, reason)
        except Exception as e:
            self.record_error(post, e)
        return self.check_spam_permissions(post)
