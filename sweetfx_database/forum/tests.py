"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from types import SimpleNamespace

from django.contrib.auth.models import User
from django.test import TestCase

from sweetfx_database.forum.laya_prefilter import (
    LayaPrefilter, domain_of, in_allowlist, preprocess,
    DEFAULT_ALLOWED_DOMAINS,
)


class SimpleTest(TestCase):
    def test_basic_addition(self):
        """
        Tests that 1 + 1 always equals 2.
        """
        self.assertEqual(1 + 1, 2)


class DomainTest(TestCase):
    def test_basic_urls(self):
        self.assertEqual(domain_of("https://www.reshade.me/forum"), "reshade.me")
        self.assertEqual(domain_of("http://t.me/somechannel"), "t.me")
        self.assertEqual(domain_of("https://yadi.sk/i/abc"), "yadi.sk")

    def test_two_level_public_suffixes(self):
        self.assertEqual(domain_of("www.example.co.uk/page"), "example.co.uk")
        self.assertEqual(domain_of("http://a.b.com.de/x"), "b.com.de")

    def test_unparseable(self):
        self.assertIsNone(domain_of("localhost"))
        self.assertIsNone(domain_of("not a url at all"))
        self.assertIsNone(domain_of("http://"))
        self.assertIsNone(domain_of(""))


class AllowlistTest(TestCase):
    def test_matches(self):
        self.assertTrue(in_allowlist("reshade.me", DEFAULT_ALLOWED_DOMAINS))
        self.assertTrue(in_allowlist("forum.reshade.me", DEFAULT_ALLOWED_DOMAINS))
        self.assertTrue(in_allowlist("thelazy.net", DEFAULT_ALLOWED_DOMAINS))

    def test_no_matches(self):
        self.assertFalse(in_allowlist("t.me", DEFAULT_ALLOWED_DOMAINS))
        self.assertFalse(in_allowlist("evil-reshade-me.com", DEFAULT_ALLOWED_DOMAINS))
        self.assertFalse(in_allowlist("", DEFAULT_ALLOWED_DOMAINS))


class PreprocessTest(TestCase):
    def test_replaces_urls_with_markers(self):
        text = ("Check https://www.reshade.me/downloads and "
                "http://t.me/spamchannel, plus "
                "<a href='https://youtube.com/watch?v=1'>video</a>")
        out = preprocess(text, DEFAULT_ALLOWED_DOMAINS)
        self.assertIn("[ok:reshade.me]", out)
        self.assertIn("[?:t.me]", out)
        self.assertIn("[ok:youtube.com]", out)
        self.assertNotIn("http", out)

    def test_no_urls_unchanged(self):
        self.assertEqual(preprocess("just a plain post", DEFAULT_ALLOWED_DOMAINS),
                         "just a plain post")


class DecideTest(TestCase):
    def make(self, **kw):
        laya = LayaPrefilter(base_url="http://laya", **kw)
        laya._predict = lambda state, question: self.score
        return laya

    def test_disabled(self):
        laya = LayaPrefilter(base_url="")
        self.assertFalse(laya.enabled)
        self.assertEqual(laya.decide("whatever"), (None, "laya disabled"))

    def test_unavailable_falls_through(self):
        laya = LayaPrefilter(base_url="http://laya")
        laya._predict = lambda state, question: None
        self.assertEqual(laya.decide("whatever"), (None, "laya unavailable"))

    def test_spam_verdict(self):
        self.score = 0.999
        action, _ = self.make().decide("buy cheap xanax now")
        self.assertEqual(action, "spam")

    def test_threshold_boundary(self):
        self.score = 0.99
        action, _ = self.make(spam_threshold=0.99).decide("spammy text")
        self.assertEqual(action, "spam")

        self.score = 0.989
        action, _ = self.make(spam_threshold=0.99).decide("spammy text")
        self.assertIsNone(action)

    def test_allowlist_veto(self):
        # High spam score, but the only link is to a known-good domain.
        self.score = 0.999
        action, reason = self.make().decide("Injector: https://yadi.sk/i/abcdef")
        self.assertIsNone(action)
        self.assertIn("all links allowed", reason)

    def test_mixed_links_no_veto(self):
        self.score = 0.999
        action, _ = self.make().decide(
            "See https://reshade.me and http://t.me/spamshop")
        self.assertEqual(action, "spam")

    def test_pass_threshold(self):
        self.score = 0.02
        action, _ = self.make(pass_threshold=0.1).decide("Thanks for the preset!")
        self.assertEqual(action, "visible")

    def test_mid_score_falls_through(self):
        self.score = 0.5
        action, _ = self.make(pass_threshold=0.1).decide("something in between")
        self.assertIsNone(action)

    def test_marker_confirm_veto(self):
        laya = LayaPrefilter(base_url="http://laya", spam_threshold=0.99,
                             require_marker_confirm=True)
        scores = iter([0.999, 0.1])
        laya._predict = lambda state, question: next(scores)
        action, _ = laya.decide("buy xanax http://t.me/shop")
        self.assertIsNone(action)

    def test_marker_confirm_agrees(self):
        laya = LayaPrefilter(base_url="http://laya", spam_threshold=0.99,
                             require_marker_confirm=True)
        scores = iter([0.999, 0.999])
        laya._predict = lambda state, question: next(scores)
        action, _ = laya.decide("buy xanax http://t.me/shop")
        self.assertEqual(action, "spam")


class FromSettingsTest(TestCase):
    def test_defaults(self):
        from sweetfx_database.forum.laya_prefilter import from_settings
        laya = from_settings(SimpleNamespace())
        self.assertFalse(laya.enabled)
        self.assertEqual(laya.spam_threshold, 0.99)
        self.assertIsNone(laya.pass_threshold)
        self.assertEqual(laya.allowed_domains, DEFAULT_ALLOWED_DOMAINS)

    def test_full(self):
        from sweetfx_database.forum.laya_prefilter import from_settings
        s = SimpleNamespace(
            LAYA_BASE_URL="http://laya:8321/",
            LAYA_SPAM_THRESHOLD=0.95,
            LAYA_PASS_THRESHOLD="0.1",
            LAYA_REQUIRE_MARKER_CONFIRM=True,
            LAYA_ALLOWED_DOMAINS=["a.com", "b.net"],
        )
        laya = from_settings(s)
        self.assertTrue(laya.enabled)
        self.assertEqual(laya.base_url, "http://laya:8321")
        self.assertEqual(laya.spam_threshold, 0.95)
        self.assertEqual(laya.pass_threshold, 0.1)
        self.assertTrue(laya.require_marker_confirm)
        self.assertEqual(laya.allowed_domains, ["a.com", "b.net"])

    def test_empty_allowed_domains_falls_back(self):
        from sweetfx_database.forum.laya_prefilter import from_settings
        laya = from_settings(SimpleNamespace(LAYA_BASE_URL="http://x",
                                             LAYA_ALLOWED_DOMAINS=[]))
        self.assertEqual(laya.allowed_domains, DEFAULT_ALLOWED_DOMAINS)


class AdminActionTest(TestCase):
    def setUp(self):
        from sweetfx_database.forum.models import Forum, ForumPost, ForumThread
        self.Forum, self.ForumPost, self.ForumThread = Forum, ForumPost, ForumThread
        self.user = User.objects.create_user(username="tester", password="x")
        self.forum = Forum.objects.create(title="Test", description="d", slug="test")
        self.thread = ForumThread.objects.create(
            forum=self.forum, creator=self.user, title="t"
        )

    def make_post(self, state=4, error_count=0):
        return self.ForumPost.objects.create(
            thread=self.thread, creator=self.user, text="hello",
            state=state, error_count=error_count,
        )

    def test_reset_error_count_action(self):
        from sweetfx_database.forum.admin import reset_error_count
        capped = self.make_post(state=4, error_count=5)
        fresh = self.make_post(state=0)
        reset_error_count(None, None, self.ForumPost.objects.filter(
            id__in=[capped.id, fresh.id]))
        capped.refresh_from_db()
        fresh.refresh_from_db()
        self.assertEqual(capped.error_count, 0)
        self.assertEqual(fresh.error_count, 0)
        # The post's state is untouched, only the counter is reset.
        self.assertEqual(capped.state, 4)

    def test_error_count_in_list_display(self):
        from sweetfx_database.forum.admin import ForumPost as ForumPostAdmin
        self.assertIn("error_count", ForumPostAdmin.list_display)
        action_names = [a.__name__ for a in ForumPostAdmin.actions]
        self.assertIn("reset_error_count", action_names)
