"""First-tier spam prefilter using the laya moderation model.

Laya (https://huggingface.co/convaiinnovations/laya) is a small (~0.6B)
moderation model served over HTTP that answers yes/no questions about a
piece of text in a few tens of milliseconds - much faster and cheaper
than the LLM path. It is meant as a first line of spam filtering: it
auto-hides the obvious spam, and everything else falls through to the
LLM (second tier) or a human.

Evaluated against 5833 labeled production posts (see laya-eval/REPORT.md):

  baseline question, score >= 0.99:  957 TP / 10 FP  (99.0% precision)
  + allowlist veto (all URLs allowed): 956 TP / 5 FP (99.5% precision)
  + marker-confirm (2nd pass, URLs -> [ok:]/[?:]): 758 TP / 1 FP (99.9%)

The allowlist veto protects legit posts whose only "suspicious" feature
is a link to a known-good domain (reshade.me, thelazy.net, youtube.com,
...). The marker-confirm pass re-scores the post with URLs replaced by
[ok:domain] / [?:domain] markers and requires it to agree before
auto-hiding; it is the most conservative option and costs a second
model call per post.

If the laya server is unreachable, every post falls through to the LLM,
so the prefilter can never break the spam pipeline.
"""
import json
import re
import urllib.request
from dataclasses import dataclass
from typing import Optional

# Domains that legit users actually share (data-driven: used by good
# posts, rarely by verified spam). Spammers use telegram, t.me, seo
# domains, social platforms - none of those are on this list.
DEFAULT_ALLOWED_DOMAINS = [
    "thelazy.net", "reshade.me", "youtube.com", "youtu.be",
    "mediafire.com", "imgur.com", "postimg.org", "photobucket.com",
    "gyazo.com", "imagebam.com", "pomf.se", "flic.kr", "noelshack.com",
    "microsoft.com", "goo.gl", "t.co", "ge.tt",
    "nexusmods.com", "steamcommunity.com", "overclock.net", "enbdev.com",
    "segmentnext.com", "forums.guru", "ninjafada.com",
    "mega.nz", "dropbox.com", "dropboxusercontent.com", "1drv.ms",
    "yadi.sk", "filedropper.com", "dodaj.rs",
    "pastebin.com", "discord.gg", "wikipedia.org",
]

BASE_QUESTION = "Is `post` spam or advertising?"
MARKER_QUESTION = (
    "Is `post` spam or advertising? "
    "[ok:X] marks a link to the trusted domain X. "
    "[?:X] marks a link to an untrusted domain X."
)

# http(s)://, www. and <a href="..."> links
URL_RE = re.compile(
    r'''(?ix)
    (?:https?://|www\.)
    ([a-z0-9\-]+(?:\.[a-z0-9\-]+)+)
    (?:[/?#][^\s"'\]<)]*)?
    |
    <a\s+href=["\']
    (?:https?://)?
    ([a-z0-9\-]+(?:\.[a-z0-9\-]+)+)
    [^\>]*>
    ''')


def domain_of(raw):
    """Extract a registrable-ish domain from a raw URL. None if unparseable."""
    raw = raw.lower()
    for pfx in ("https://", "http://", "www."):
        if raw.startswith(pfx):
            raw = raw[len(pfx):]
    raw = raw.rstrip(".")
    if "/" in raw:
        raw = raw.split("/", 1)[0]
    if not raw or " " in raw:
        return None
    parts = raw.split(".")
    if len(parts) < 2:
        return None
    if not all(re.fullmatch(r"[a-z0-9\-]+", p) for p in parts):
        return None
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "gov", "ac"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def in_allowlist(domain, allowlist):
    for a in allowlist:
        if domain == a or domain.endswith("." + a) or a.endswith("." + domain):
            return True
    return False


def preprocess(text, allowlist):
    """Replace URLs with [ok:domain] / [?:domain] markers."""
    def repl(m):
        d = domain_of(m.group(1) or m.group(2))
        if d is None:
            return m.group(0)
        return "[ok:%s]" % d if in_allowlist(d, allowlist) else "[?:%s]" % d
    return URL_RE.sub(repl, text)


class LayaPrefilter:
    def __init__(self, base_url, spam_threshold=0.99, pass_threshold=None,
                 allowed_domains=None, require_marker_confirm=False,
                 timeout=5.0):
        self.base_url = (base_url or "").rstrip("/")
        self.spam_threshold = spam_threshold
        self.pass_threshold = pass_threshold
        self.allowed_domains = allowed_domains or DEFAULT_ALLOWED_DOMAINS
        self.require_marker_confirm = require_marker_confirm
        self.timeout = timeout

    @property
    def enabled(self):
        return bool(self.base_url)

    def _predict(self, state, question):
        """One prediction. Returns noul in [0,1] (P(spam)) or None on error."""
        payload = json.dumps({
            "states": [state],
            "questions": {"spam": {"type": "noul", "instructions": question}},
        }).encode("utf-8")
        req = urllib.request.Request(
            self.base_url + "/predict/bulk", data=payload,
            headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return float(data["results"][0]["answers"]["spam"]["noul"])
        except Exception:
            return None

    def score(self, text):
        """Baseline score of the raw post."""
        return self._predict({"post": text}, BASE_QUESTION)

    def score_markers(self, text):
        """Score with URLs replaced by trusted/untrusted markers."""
        return self._predict({"post": preprocess(text, self.allowed_domains)},
                             MARKER_QUESTION)

    def decide(self, text):
        """Decide what to do with a post.

        Returns a LayaVerdict where action is:
          "spam"    - auto-hide the post
          "visible" - mark visible without asking the LLM
                      (only when pass_threshold is set and score is below it)
          None      - no decision, pass on to the next tier (LLM)
        and score is the baseline laya spam score (None if unavailable).
        """
        if not self.enabled:
            return LayaVerdict(None, "laya disabled", None)

        s = self.score(text)
        if s is None:
            return LayaVerdict(None, "laya unavailable", None)

        if s >= self.spam_threshold:
            # Allowlist veto: a post whose links are all to known-good
            # domains is not auto-hidden (protects legit link sharing).
            if self._all_links_allowed(text):
                return LayaVerdict(None, "laya %.3f but all links allowed" % s,
                                   s)
            if self.require_marker_confirm:
                s2 = self.score_markers(text)
                if s2 is not None and s2 < self.spam_threshold:
                    return LayaVerdict(
                        None, "laya %.3f but marker-confirm %.3f" % (s, s2), s)
            return LayaVerdict("spam", "laya prefilter score %.3f" % s, s)

        if self.pass_threshold is not None and s < self.pass_threshold:
            return LayaVerdict(
                "visible", "laya prefilter score %.3f below %.2f" % (
                    s, self.pass_threshold), s)

        return LayaVerdict(None, "laya %.3f, to LLM" % s, s)

    def _all_links_allowed(self, text):
        """True if the post has at least one URL and every domain is allowed."""
        domains = [domain_of(m.group(1) or m.group(2))
                   for m in URL_RE.finditer(text)]
        domains = [d for d in domains if d]
        return bool(domains) and all(in_allowlist(d, self.allowed_domains)
                                     for d in domains)


@dataclass
class LayaVerdict:
    """Outcome of LayaPrefilter.decide().

    action: "spam", "visible", or None (fall through to the next tier)
    reason: human-readable explanation (stored as state_reason)
    score:  baseline laya spam score in [0,1], None if unavailable
    """
    action: object
    reason: str
    score: Optional[float]


def from_settings(settings):
    """Build a prefilter from Django settings (SFX_LAYA_* env vars)."""
    pass_thr = getattr(settings, "LAYA_PASS_THRESHOLD", "")
    return LayaPrefilter(
        base_url=getattr(settings, "LAYA_BASE_URL", ""),
        spam_threshold=getattr(settings, "LAYA_SPAM_THRESHOLD", 0.99),
        pass_threshold=float(pass_thr) if pass_thr else None,
        allowed_domains=getattr(settings, "LAYA_ALLOWED_DOMAINS", None)
                        or DEFAULT_ALLOWED_DOMAINS,
        require_marker_confirm=getattr(
            settings, "LAYA_REQUIRE_MARKER_CONFIRM", False),
    )
