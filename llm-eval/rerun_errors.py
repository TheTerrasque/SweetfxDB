# -*- coding: utf-8 -*-
"""Re-run posts that ended in an error (429 rate-limit or JSON parse) in the
full eval, with proper backoff, and merge the results back into
results_<config>.jsonl.

The 429s in the original run were a load-test artifact (12 concurrent
requests against the shared lllm.thelazy.net proxy, single 3s retry).
Production calls are sequential, so 429s are not a production property.
Parse failures ARE a production property (production does not retry and the
post would sit in state 4), so first-attempt error counts are snapshotted
to first_attempt_errors.json before overwriting.

Usage: python rerun_errors.py [--concurrency 4]
"""
import argparse
import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import run_eval  # noqa: E402  (module-level: loads key, sample, prompts)

from openai import OpenAI  # noqa: E402

ROOT = run_eval.ROOT
CONFIGS = run_eval.CONFIGS
EXPECTED = run_eval.EXPECTED

RATE_BACKOFF = [10, 20, 30, 60, 120, 180]   # seconds between 429 retries
PARSE_TRIES = 3                             # total attempts for parse errors
MAX_TRIES = 8


def judge_with_backoff(client, cfg, prompt):
    """Call the LLM, retrying with backoff.
    Returns (wanted, rating, reason, latency_ms, usage, err, n_attempts)."""
    last = ("", None, "", 0, {}, "gave up", 0)
    for attempt in range(1, MAX_TRIES + 1):
        wanted, rating, reason, latency, usage, err = \
            run_eval.judge(client, cfg, prompt)
        last = (wanted, rating, reason, latency, usage, err, attempt)
        if err is None:
            return last
        is_rate = "429" in err or "RateLimit" in err
        is_parse = err.startswith("parse")
        if is_rate:
            if attempt > len(RATE_BACKOFF):
                break
            time.sleep(RATE_BACKOFF[attempt - 1])
        elif is_parse:
            if attempt >= PARSE_TRIES:
                break
            time.sleep(2)
        else:
            if attempt > 4:
                break
            time.sleep(10 * attempt)
    return last


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--configs", default="qwen-default,qwen-medium,"
                    "qwen-low,qwen-nothink")
    args = ap.parse_args()
    names = [c.strip() for c in args.configs.split(",") if c.strip()]

    client = OpenAI(base_url=run_eval.BASE_URL, api_key=run_eval.KEY)

    for name in names:
        cfg = CONFIGS[name]
        path = os.path.join(ROOT, "results_%s.jsonl" % name)
        recs = [json.loads(l) for l in open(path, encoding="utf-8")]
        by_id = {r["id"]: r for r in recs}

        # snapshot first-attempt errors (production-equivalent failure rate)
        snap_path = os.path.join(ROOT, "first_attempt_errors.json")
        snap = {}
        if os.path.exists(snap_path):
            snap = json.load(open(snap_path, encoding="utf-8"))
        errs = [r for r in recs if r["error"]]
        snap[name] = [{"id": r["id"], "state": r["state"],
                       "error": r["error"][:200]} for r in errs]
        json.dump(snap, open(snap_path, "w", encoding="utf-8"), indent=1)

        if not errs:
            print("%s: no errors to re-run" % name, file=sys.stderr)
            continue
        print("%s: re-running %d error posts (model=%s)"
              % (name, len(errs), cfg["model"]), file=sys.stderr)

        # map id -> sample record for prompt building
        sample = {p["id"]: p for p in run_eval.SAMPLE}

        def work(r):
            p = sample[r["id"]]
            prompt = run_eval.build_prompt(p)
            wanted, rating, reason, latency, usage, err, n = \
                judge_with_backoff(client, cfg, prompt)
            nr = dict(r)
            nr.update(wanted=wanted, rating=rating, reason=reason,
                      latency_ms=latency, usage=usage, error=err,
                      retries=n)
            return nr

        fixed = still = 0
        with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
            futs = {ex.submit(work, r): r for r in errs}
            for i, fut in enumerate(as_completed(futs), 1):
                nr = fut.result()
                by_id[nr["id"]] = nr
                if nr["error"]:
                    still += 1
                else:
                    fixed += 1
                if i % 20 == 0 or i == len(futs):
                    print("  %d/%d (fixed %d, still failing %d)"
                          % (i, len(futs), fixed, still), file=sys.stderr)

        with open(path, "w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(by_id[r["id"]]) + "\n")
        print("%s: done. fixed=%d still_error=%d" % (name, fixed, still),
              file=sys.stderr)


if __name__ == "__main__":
    main()
