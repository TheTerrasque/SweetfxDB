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
    # permissions_to_remove = ["post_on_forum", "post_on_games"] # Deprecated by parametrized method
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

    def remove_user_posting_permissions(self, user: fm.userdb.User, permission_codename: str, app_label: str):
        try:
            # app_label might be 'forum' or 'gamedb'
            permission = fm.Permission.objects.get(codename=permission_codename, content_type__app_label=app_label)
            user.user_permissions.remove(permission)
        except fm.Permission.DoesNotExist:
            # Handle case where permission doesn't exist, maybe log an error
            print(f"Permission {app_label}.{permission_codename} not found.")
        except Exception as e:
            # Handle other potential errors
            print(f"Error removing permission {app_label}.{permission_codename} for user {user.username}: {str(e)}")

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
                self.remove_user_posting_permissions(post.creator, permission_codename='post_on_forum', app_label='forum')
                return 2
            return 1
        return 0

    def judge_game(self, game: gm.Game):
        if not self.active: return -1

        game_text_content = f"Title: {game.title}\nSweetFX Notes: {game.sweetfx_notes}"
        # Assuming self.post_template can be used by passing the game_text_content as 'post.text' equivalent
        # The template expects an object with a 'text' attribute.
        # We can create a simple object or dictionary that mimics this structure if needed.
        # For now, let's assume the template can handle a direct string or we adapt the template rendering.
        # Let's try structuring it like the post object for the template:
        class TempContent:
            def __init__(self, text):
                self.text = text

        prompt = self.post_template.render(RULES=self.rules, post=TempContent(game_text_content))
        
        try:
            response = self.call_llm_and_get_response(prompt)
            # Assuming response["rating"] gives values like UNCHECKED, VISIBLE, SUSPECTED_SPAM etc.
            # The current call_llm_and_get_response maps yes:1 (VISIBLE), no:2 (SUSPECTED_SPAM), maybe:3 (UNSURE)
            # This needs to align with gm.GAME_PRESET_STATE_CHOICES numeric values.
            # yes: VISIBLE (1), no: SUSPECTED_SPAM (2), maybe: UNSURE (3)
            # This mapping is consistent with the first few states.
            game.update_state(response["rating"], response["reason"])
        except Exception as e:
            game.update_state(gm.ERROR, str(e)) # gm.ERROR is 4

        if game.state in gm.GAMES_PRESETS_SPAM_STATES:
            num_spams = gm.Game.objects.filter(state__in=gm.GAMES_PRESETS_SPAM_STATES, creator=game.creator).count()
            # Ensure GAMES_PRESETS_VISIBLE_STATES is appropriate for this check
            num_nonspams = gm.Game.objects.filter(state__in=gm.GAMES_PRESETS_VISIBLE_STATES, creator=game.creator).count()
            if num_spams > num_nonspams:
                self.remove_user_posting_permissions(game.creator, permission_codename='post_on_games', app_label='gamedb')
                return 2 # User lost rights
            return 1 # Spam, but user kept rights
        return 0 # Not spam

    def judge_preset(self, preset: gm.Preset):
        if not self.active: return -1

        preset_text_content = f"Title: {preset.title}\nDescription: {preset.description}\nSettings: {preset.settings_text}"
        
        # Using the same TempContent helper as in judge_game
        class TempContent:
            def __init__(self, text):
                self.text = text

        prompt = self.post_template.render(RULES=self.rules, post=TempContent(preset_text_content))
        
        try:
            response = self.call_llm_and_get_response(prompt)
            # Mapping: yes: VISIBLE (1), no: SUSPECTED_SPAM (2), maybe: UNSURE (3)
            preset.update_state(response["rating"], response["reason"])
        except Exception as e:
            preset.update_state(gm.ERROR, str(e)) # gm.ERROR is 4

        if preset.state in gm.GAMES_PRESETS_SPAM_STATES:
            num_spams = gm.Preset.objects.filter(state__in=gm.GAMES_PRESETS_SPAM_STATES, creator=preset.creator).count()
            num_nonspams = gm.Preset.objects.filter(state__in=gm.GAMES_PRESETS_VISIBLE_STATES, creator=preset.creator).count()
            if num_spams > num_nonspams:
                # Note: Using 'post_on_games' permission, as presets are part of the gamedb
                self.remove_user_posting_permissions(preset.creator, permission_codename='post_on_games', app_label='gamedb')
                return 2 # User lost rights
            return 1 # Spam, but user kept rights
        return 0 # Not spam
