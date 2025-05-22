import openai
import json
import jinja2
from django.conf import settings
from django.contrib.auth.models import Permission
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
GAME_PROMPT = getattr(settings, "DEFAULT_GAME_PROMPT", "Is the following game submission spam or unwanted content based on these rules: {{ RULES }}\n\nGame Title: {{ game.title }}\nGame Description: {{ game.description }}\nSweetFX Notes: {{ game.sweetfx_notes }}\nCreator: {{ game.creator.username }}")
PRESET_PROMPT = getattr(settings, "DEFAULT_PRESET_PROMPT", "Is the following preset submission spam or unwanted content based on these rules: {{ RULES }}\n\nPreset Title: {{ preset.title }}\nPreset Description: {{ preset.description }}\nPreset Settings:\n{{ preset.settings_text }}\nCreator: {{ preset.creator.username }}")

RESPONSE_FORMAT = """ Give the answer in json: { "wanted": "yes|no|maybe", "reason":"<reason>"}"""

class OpenAISpamJudge:
    active = False
    def __init__(self, base_url = BASE_URL, key=KEY, model=MODEL, args=ARGS, rules=RULES, post_prompt=POST_PROMPT, thread_prompt = THREAD_PROMPT, game_prompt=GAME_PROMPT, preset_prompt=PRESET_PROMPT):
        if key and model and rules and post_prompt and thread_prompt and game_prompt and preset_prompt:
            self.client = openai.OpenAI(api_key=key, base_url=base_url)
            self.post_template = jinja2.Template(post_prompt + RESPONSE_FORMAT)
            self.thread_template = jinja2.Template(thread_prompt + RESPONSE_FORMAT)
            self.game_template = jinja2.Template(game_prompt + RESPONSE_FORMAT)
            self.preset_template = jinja2.Template(preset_prompt + RESPONSE_FORMAT)
            self.rules = rules
            self.model = model
            self.args = args
            self.active = True

    def remove_user_posting_permissions(self, user: fm.userdb.User, permission_codename: str):
        try:
            permission = Permission.objects.get(codename=permission_codename)
            user.user_permissions.remove(permission)
        except Permission.DoesNotExist:
            print(f"Warning: Permission '{permission_codename}' not found.") # Or log this
        except Exception as e:
            print(f"Error removing permission '{permission_codename}' for user '{user.username}': {e}") # Or log

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
                self.remove_user_posting_permissions(post.creator, 'post_on_forum')
                return 2
            return 1
        return 0

    def judge_game(self, game: gm.Game):
        if not self.active: return -1

        prompt = self.game_template.render(RULES=self.rules, game=game)
        try:
            response = self.call_llm_and_get_response(prompt)
            game.update_state(response["rating"], response["reason"])
        except Exception as e:
            game.update_state(4, str(e))

        if game.state in gm.POST_SPAM_STATES:
            num_spams = gm.Game.objects.filter(state__in=gm.POST_SPAM_STATES, creator=game.creator).count()
            num_nonspams = gm.Game.objects.filter(state__in=gm.POSTS_VISIBLE_STATES, creator=game.creator).count()
            if num_spams > num_nonspams:
                self.remove_user_posting_permissions(game.creator, permission_codename='post_on_games')
                return 2
            return 1
        return 0

    def judge_preset(self, preset: gm.Preset):
        if not self.active: return -1

        prompt = self.preset_template.render(RULES=self.rules, preset=preset)
        try:
            response = self.call_llm_and_get_response(prompt)
            preset.update_state(response["rating"], response["reason"])
        except Exception as e:
            preset.update_state(4, str(e))

        if preset.state in gm.POST_SPAM_STATES:
            num_spams = gm.Preset.objects.filter(state__in=gm.POST_SPAM_STATES, creator=preset.creator).count()
            num_nonspams = gm.Preset.objects.filter(state__in=gm.POSTS_VISIBLE_STATES, creator=preset.creator).count()
            if num_spams > num_nonspams:
                self.remove_user_posting_permissions(preset.creator, permission_codename='post_on_games')
                return 2
            return 1
        return 0
