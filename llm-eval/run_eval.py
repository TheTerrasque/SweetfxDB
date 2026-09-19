# -*- coding: utf-8 -*-
"""Evaluate LLM configs on the sweetfx forum spam-judgment task.

Replays the exact production prompt (FORUM_RULES + DEFAULT_POST_PROMPT from
sweetfx_database/settings.py, plus RESPONSE_FORMAT from
gamedb/openai_spamjudge.py, rendered with jinja2 against
post/thread/forum/creator context) against:

  - mistral-small-2501   (production baseline, temp 0.1, timeout 60s)
  - Qwen-Latest          (default, thinking on)
  - Qwen-Latest + reasoning_effort medium
  - Qwen-Latest + reasoning_effort low
  - Qwen-Latest + chat_template_kwargs enable_thinking=false

Ground truth: state 1 (Visible) => wanted=yes; state 2/5 (Spam/Verified
spam) => wanted=no; state 3 (Unsure) => wanted=maybe.

The response parse replicates production exactly:
  content.strip() -> re.sub("```[a-zA-Z]*", "") -> strip("`\\n") ->
  json.loads -> strict {"yes":1,"no":2,"maybe":3}[wanted]
so a "Yes" or "NO" counts as a production error (post would land in
state 4).

Progress is saved incrementally to results_<config>.jsonl so a run can be
resumed after a crash.

Usage: python run_eval.py [--limit N] [--concurrency 12]
"""
import argparse
import ast
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import jinja2
from openai import OpenAI

ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_URL = "https://lllm.thelazy.net"
KEY = open(os.path.join(ROOT, ".key")).read().strip()
SAMPLE = json.load(open(os.path.join(ROOT, "sample.json")))

# ---------------------------------------------------------------- settings.py
# Extract the exact prompt constants without importing Django.
SETTINGS = os.path.join(ROOT, "..", "sweetfx_database", "settings.py")
src = open(SETTINGS, encoding="utf-8").read()
tree = ast.parse(src)
consts = {}
for node in tree.body:
    if isinstance(node, ast.Assign) and len(node.targets) == 1 \
            and isinstance(node.targets[0], ast.Name) \
            and node.targets[0].id in ("FORUM_RULES", "DEFAULT_POST_PROMPT"):
        consts[node.targets[0].id] = ast.literal_eval(node.value)
FORUM_RULES = consts["FORUM_RULES"]
POST_PROMPT = consts["DEFAULT_POST_PROMPT"]

# RESPONSE_FORMAT lives in openai_spamjudge.py (line 18)
RESPONSE_FORMAT = (
    """ Give the answer in json: { "wanted": "yes|no|maybe", "reason":"<reason>"}"""
)
print("prompt chars: rules=%d post=%d format=%d" % (
    len(FORUM_RULES), len(POST_PROMPT), len(RESPONSE_FORMAT)), file=sys.stderr)


class PostView(object):
    """Mirror of the model __str__ chain used by the jinja prompt:
    post.thread.forum -> Forum.title, post.thread -> ForumThread.title,
    post.creator -> User.__str__ = username, post.text."""

    def __init__(self, rec):
        self.forum = rec["forum"]
        self.thread = rec["thread"]
        self.creator = rec["creator"]
        self.text = rec["text"]


def build_prompt(rec):
    tmpl = jinja2.Template(POST_PROMPT + RESPONSE_FORMAT)
    return tmpl.render(RULES=FORUM_RULES, post=PostView(rec))


# ------------------------------------------------------------------ configs
CONFIGS = {
    # production as-is
    "mistral": dict(model="mistral-small-2501", temperature=0.1,
                    timeout=60, extra_body=None),
    # qwen default: thinking on, whatever the model default is
    "qwen-default": dict(model="Qwen-Latest", temperature=0.1,
                         timeout=300, extra_body=None),
    "qwen-medium": dict(model="Qwen-Latest", temperature=0.1,
                        timeout=300, reasoning_effort="medium"),
    "qwen-low": dict(model="Qwen-Latest", temperature=0.1,
                     timeout=300, reasoning_effort="low"),
    "qwen-nothink": dict(model="Qwen-Latest", temperature=0.1,
                         timeout=300,
                         extra_body={"chat_template_kwargs":
                                     {"enable_thinking": False}}),
}

EXPECTED = {1: "yes", 2: "no", 3: "maybe", 5: "no"}


def judge(client, cfg, prompt):
    """One LLM call with production-style parse.
    Returns (wanted_raw, rating, reason, latency_ms, usage, err).
    rating is 1/2/3 like production, None if the parse failed."""
    kwargs = dict(model=cfg["model"], timeout=cfg["timeout"],
                  messages=[{"role": "user", "content": prompt}])
    if cfg.get("temperature") is not None:
        kwargs["temperature"] = cfg["temperature"]
    if cfg.get("reasoning_effort"):
        kwargs["reasoning_effort"] = cfg["reasoning_effort"]
        kwargs["extra_body"] = {
            "allowed_openai_params": ["reasoning_effort"],
        }
    if cfg.get("extra_body"):
        kwargs["extra_body"] = dict(kwargs.get("extra_body") or {})
        kwargs["extra_body"].update(cfg["extra_body"])

    t0 = time.time()
    try:
        resp = client.chat.completions.create(**kwargs)
        latency = int((time.time() - t0) * 1000)
        msg = resp.choices[0].message
        usage = getattr(resp, "usage", None)
        u = dict(
            prompt_tokens=usage.prompt_tokens if usage else None,
            completion_tokens=usage.completion_tokens if usage else None,
        )
        det = getattr(usage, "completion_tokens_details", None) if usage else None
        u["reasoning_tokens"] = getattr(det, "reasoning_tokens", None) if det else None
        # production parse, verbatim
        result = (msg.content or "").strip()
        result = re.sub(r"```[a-zA-Z]*", "", result).strip("`" + "\n")
        try:
            j = json.loads(result)
            wanted = j["wanted"]
            rating = {"yes": 1, "no": 2, "maybe": 3}[wanted]
            reason = str(j.get("reason", ""))[:300]
            return wanted, rating, reason, latency, u, None
        except (ValueError, TypeError, KeyError) as e:
            return "", None, result[:200], latency, u, \
                "parse: %s: %s" % (type(e).__name__, str(e)[:100])
    except Exception as e:
        latency = int((time.time() - t0) * 1000)
        return "", None, "", latency, {}, "%s: %s" % (type(e).__name__, str(e)[:200])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0,
                    help="limit posts per config (pilot mode)")
    ap.add_argument("--concurrency", type=int, default=12)
    ap.add_argument("--configs", default="",
                    help="comma-separated config names (default: all)")
    args = ap.parse_args()

    if args.configs:
        wanted = [c.strip() for c in args.configs.split(",") if c.strip()]
        selected = {k: v for k, v in CONFIGS.items() if k in wanted}
    else:
        selected = CONFIGS

    client = OpenAI(base_url=BASE_URL, api_key=KEY)
    posts = SAMPLE
    if args.limit:
        posts = posts[:args.limit]
    print("sample: %d posts, concurrency %d" % (len(posts), args.concurrency),
          file=sys.stderr)

    for name, cfg in selected.items():
        out_path = os.path.join(ROOT, "results_%s.jsonl" % name)
        done = {}
        if os.path.exists(out_path):
            with open(out_path) as f:
                for line in f:
                    r = json.loads(line)
                    done[r["id"]] = r
        todo = [p for p in posts if p["id"] not in done]
        if not todo:
            print("%s: all %d done, skipping" % (name, len(posts)),
                  file=sys.stderr)
            continue
        print("%s: %d to do (model=%s)" % (name, len(todo), cfg["model"]),
              file=sys.stderr)

        out = open(out_path, "a")
        n_err = 0

        def work(p):
            prompt = build_prompt(p)
            wanted, rating, reason, latency, usage, err = judge(
                client, cfg, prompt)
            if err and not err.startswith("parse"):
                time.sleep(3)
                wanted, rating, reason, latency, usage, err = judge(
                    client, cfg, prompt)
            rec = dict(id=p["id"], state=p["state"],
                       expected=EXPECTED[p["state"]],
                       wanted=wanted, rating=rating,
                       reason=reason, latency_ms=latency, usage=usage,
                       error=err)
            return rec

        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = {ex.submit(work, p): p for p in todo}
            for i, fut in enumerate(as_completed(futs), 1):
                rec = fut.result()
                if rec["error"]:
                    n_err += 1
                out.write(json.dumps(rec) + "\n")
                out.flush()
                if i % 25 == 0 or i == len(futs):
                    print("  %d/%d (errors so far: %d)" %
                          (i, len(futs), n_err), file=sys.stderr)
        out.close()


if __name__ == "__main__":
    main()
