#!/usr/bin/env python3
"""Analyze the Qwen-Latest vs Mistral forum-spam eval results.

Usage: python llm-eval/analyze_llm.py
Reads llm-eval/results_<config>.jsonl and llm-eval/sample_posts.json.
"""
import json, os, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIGS = ["mistral", "qwen-default", "qwen-medium", "qwen-low", "qwen-nothink"]

def load(name):
    path = os.path.join(HERE, f"results_{name}.jsonl")
    if not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            out[r["id"]] = r
    return out

def norm(r):
    """Normalize old/new record schema to a common dict."""
    if "ok" in r:  # new schema
        return {
            "id": r["id"], "state": r["state"],
            "ok": r["ok"], "wanted": r["wanted"],
            "lat_ms": r.get("lat_ms") or 0,
            "reasoning_tokens": r.get("reasoning_tokens") or 0,
            "completion_tokens": r.get("completion_tokens") or 0,
            "error": r.get("error"),
        }
    # old schema
    usage = r.get("usage") or {}
    return {
        "id": r["id"], "state": r["state"],
        "ok": r.get("error") is None,
        "wanted": r.get("wanted"),
        "lat_ms": r.get("latency_ms") or 0,
        "reasoning_tokens": usage.get("reasoning_tokens") or 0,
        "completion_tokens": usage.get("completion_tokens") or 0,
        "error": r.get("error"),
    }

def main():
    with open(os.path.join(HERE, "sample_posts.json"), encoding="utf-8") as f:
        posts = json.load(f)
    states = {
        "good  (state 1)": [p for p in posts if p["state"] == 1],
        "bad   (state 5)": [p for p in posts if p["state"] == 5],
        "bad   (state 2)": [p for p in posts if p["state"] == 2],
        "unsure(state 3)": [p for p in posts if p["state"] == 3],
    }
    print(f"sample: {len(posts)} posts")
    print()

    header = (f"{'config':<14} {'state':<14} {'n':>4} {'ok':>4} {'err':>4} "
              f"{'spam%':>6} {'vis%':>6} {'mb%':>6} {'err%':>6}")
    print(header)
    print("-" * len(header))

    for cfg in CONFIGS:
        res = {i: norm(r) for i, r in load(cfg).items()}
        if not res:
            print(f"{cfg:<14} (no results yet)")
            continue
        for label, group in states.items():
            n = len(group)
            ok = sum(1 for p in group if p["id"] in res and res[p["id"]]["ok"])
            err = sum(1 for p in group if p["id"] in res and not res[p["id"]]["ok"])
            wanted = {}
            for p in group:
                r = res.get(p["id"])
                if r and r["ok"]:
                    wanted[r["wanted"]] = wanted.get(r["wanted"], 0) + 1
            def pct(k):
                return f"{100*wanted.get(k,0)/max(ok,1):.1f}"
            print(f"{cfg:<14} {label:<14} {n:>4} {ok:>4} {err:>4} "
                  f"{pct('no'):>6} {pct('yes'):>6} {pct('maybe'):>6} {pct('error'):>6}")
        lats = sorted(r["lat_ms"] for r in res.values() if r["ok"])
        rts = [r["reasoning_tokens"] for r in res.values() if r["ok"]]
        cts = [r["completion_tokens"] for r in res.values() if r["ok"]]
        if lats:
            p50 = lats[len(lats)//2]
            p95 = lats[int(len(lats)*0.95)]
            print(f"{cfg:<14} {'latency':<14} {len(lats):>4} {'':>4} {'':>4} "
                  f"p50={p50}ms p95={p95}ms  reasoning_tok med={statistics.median(rts):.0f} max={max(rts)}  compl_tok avg={sum(cts)/len(cts):.0f}")
        print()

    print("=== FALSE POSITIVES: good posts judged spam (wanted=no) ===")
    for cfg in CONFIGS:
        res = {i: norm(r) for i, r in load(cfg).items()}
        grp = states["good  (state 1)"]
        fps = [p for p in grp if p["id"] in res and res[p["id"]]["ok"] and res[p["id"]]["wanted"] == "no"]
        n_good = len(grp)
        print(f"{cfg:<14} {len(fps)}/{n_good} = {100*len(fps)/n_good:.2f}%")
        for p in fps[:10]:
            r = res[p["id"]]
            text = p["text"].replace("\n", " ")[:70]
            print(f"    id={p['id']} forum={p['forum'][:14]:<14} {text}")
        print()

    print("=== RECALL: bad posts (state 5) judged spam (wanted=no) ===")
    for cfg in CONFIGS:
        res = {i: norm(r) for i, r in load(cfg).items()}
        grp = states["bad   (state 5)"]
        judged = [p for p in grp if p["id"] in res and res[p["id"]]["ok"]]
        spam = [p for p in judged if res[p["id"]]["wanted"] == "no"]
        maybe = [p for p in judged if res[p["id"]]["wanted"] == "maybe"]
        vis = [p for p in judged if res[p["id"]]["wanted"] == "yes"]
        print(f"{cfg:<14} spam={len(spam)}/{len(judged)} ({100*len(spam)/max(len(judged),1):.1f}%)  "
              f"maybe={len(maybe)}  visible={len(vis)}")
    print()

    print("=== ERRORS (would be state 4 in production) ===")
    for cfg in CONFIGS:
        res = {i: norm(r) for i, r in load(cfg).items()}
        errs = [r for r in res.values() if not r["ok"]]
        kinds = {}
        for r in errs:
            k = (r["error"] or "?").split(":")[0][:35]
            kinds[k] = kinds.get(k, 0) + 1
        if errs:
            print(f"{cfg:<14} {len(errs)}/{len(res)}  {kinds}")
        else:
            print(f"{cfg:<14} 0/{len(res)}")

if __name__ == "__main__":
    main()
