"""
Tests for the gamedb app: OpenAI spam judge error handling/retry and
the process_forum_spam pending-post selection.
"""

from django.contrib.auth.models import User
from django.test import TestCase

from sweetfx_database.forum.models import Forum, ForumPost, ForumThread
from sweetfx_database.gamedb.management.commands.process_forum_spam import pending_posts
from sweetfx_database.gamedb.openai_spamjudge import OpenAISpamJudge


def make_judge(**overrides):
    kwargs = dict(
        base_url="http://localhost:9/v1",
        key="test-key",
        model="test-model",
        args={"temperature": 0.1, "timeout": 60},
        rules="RULES",
        post_prompt="P {{post.text}}",
        thread_prompt="T {{post.thread.title}}",
    )
    kwargs.update(overrides)
    return OpenAISpamJudge(**kwargs)


class SpamJudgeSetupTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="tester", password="x")
        self.forum = Forum.objects.create(title="Test", description="d", slug="test")
        self.thread = ForumThread.objects.create(
            forum=self.forum, creator=self.user, title="t"
        )

    def make_post(self, state=0, state_reason=""):
        return ForumPost.objects.create(
            thread=self.thread,
            creator=self.user,
            text="hello",
            state=state,
            state_reason=state_reason,
        )


class JudgePostTest(SpamJudgeSetupTest):
    def test_inactive_judge_returns_none_and_keeps_state(self):
        post = self.make_post()
        judge = OpenAISpamJudge(
            base_url=None, key=None, model=None, args=None,
            rules=None, post_prompt=None, thread_prompt=None,
        )
        self.assertFalse(judge.active)
        self.assertIsNone(judge.judge_post(post))
        post.refresh_from_db()
        self.assertEqual(post.state, 0)

    def test_none_args_falls_back_to_settings_default(self):
        # The command passes args=None when --timeout is not given;
        # the judge must then use the settings-derived default ARGS.
        from sweetfx_database.gamedb.openai_spamjudge import ARGS
        judge = make_judge(args=None)
        self.assertEqual(judge.args, ARGS)

    def test_error_keeps_post_in_state_4(self):
        post = self.make_post()
        judge = make_judge()
        judge.call_llm_and_get_response = lambda prompt: 1/0
        self.assertEqual(judge.judge_post(post), 0)
        post.refresh_from_db()
        self.assertEqual(post.state, 4)
        self.assertTrue(post.state_reason.startswith("LLM judgment error:"))

    def test_error_is_retried_on_next_round(self):
        # A post that failed once stays in state 4, so the next cron
        # run picks it up again; when the LLM succeeds on a later
        # round the post gets a real verdict.
        post = self.make_post()
        judge = make_judge()
        judge.call_llm_and_get_response = lambda prompt: 1/0
        judge.judge_post(post)
        post.refresh_from_db()
        pending = set(pending_posts().values_list("id", flat=True))
        self.assertIn(post.id, pending)
        judge.call_llm_and_get_response = lambda prompt: {
            "wanted": "no", "reason": "spam", "rating": 2,
        }
        judge.judge_post(post)
        post.refresh_from_db()
        self.assertEqual(post.state, 2)
        self.assertEqual(post.state_reason, "spam")
        self.assertNotIn(post.id, set(pending_posts().values_list("id", flat=True)))

    def test_error_is_retried_indefinitely(self):
        # No attempt limit: a post that keeps failing stays in state
        # 4 and is retried on every cron round until it succeeds.
        post = self.make_post()
        judge = make_judge()
        judge.call_llm_and_get_response = lambda prompt: 1/0
        for _ in range(5):
            judge.judge_post(post)
            post.refresh_from_db()
            self.assertEqual(post.state, 4)
            self.assertIn(
                post.id, set(pending_posts().values_list("id", flat=True))
            )
        judge.call_llm_and_get_response = lambda prompt: {
            "wanted": "yes", "reason": "wanted", "rating": 1,
        }
        judge.judge_post(post)
        post.refresh_from_db()
        self.assertEqual(post.state, 1)


class PendingPostsTest(SpamJudgeSetupTest):
    def test_query_selection(self):
        p0 = self.make_post(state=0)
        p1 = self.make_post(state=1)
        p2 = self.make_post(state=2)
        p4 = self.make_post(
            state=4, state_reason="LLM judgment error: Expecting value: line 1 column 1"
        )
        p4x = self.make_post(state=4, state_reason="something else")
        # New posts (state 0) and all error posts (state 4) are
        # selected; visible/spam/verified posts are not. State 0 comes
        # first so new posts are judged before old errors.
        ids = list(pending_posts().values_list("id", flat=True))
        self.assertEqual(set(ids), {p0.id, p4.id, p4x.id})
        self.assertEqual(ids[0], p0.id)
