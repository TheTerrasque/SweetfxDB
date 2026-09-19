# Qwen-Latest vs mistral-small-2501 — forum spam judge evaluation

Date: 2026-09-19 · Endpoint: https://lllm.thelazy.net (LiteLLM proxy, Qwen-Latest → qwen3.8-27b, vLLM)
Prompt: byte-identical to production (`FORUM_RULES` + `DEFAULT_POST_PROMPT` + `RESPONSE_FORMAT` from
`settings.py` / `gamedb/openai_spamjudge.py`), rendered per post with forum/thread/creator context
re-exported from the production database.

## Sample

1228 labeled posts, fixed seed 42: 600 state 1 (Visible, good), 600 state 5 (Verified spam),
all 11 state 2 (Spam), all 17 state 3 (Unsure). One state-2 post (40775) had its creator user
deleted from production; it was judged with empty forum/thread/creator context (in production,
`{{post.creator}}` would raise for it — see "Pre-existing production bug" below).

## Configs

| Config | Request |
|---|---|
| `mistral` | mistral-small-2501, temperature 0.1, timeout 60 s (production settings) |
| `qwen-default` | Qwen-Latest, no extra params (exactly what production code sends today) |
| `qwen-medium` | Qwen-Latest, `reasoning_effort=medium` (+ `allowed_openai_params`) |
| `qwen-low` | Qwen-Latest, `reasoning_effort=low` |
| `qwen-nothink` | Qwen-Latest, `chat_template_kwargs={enable_thinking: false}` |

All calls retried with backoff (429) and on parse failure; final data has **0 errors across all
6,140 calls** (576 first-attempt failures — 429s and malformed-JSON parse errors — all succeeded
on retry, i.e. the parse failures are stochastic, not deterministic).

## Results

| Config | Good: flagged spam | Good: maybe | Bad (s5): spam | Bad (s5): visible | Bad (s5): maybe | Latency p50 / p95 / p99 / max | Calls > 60 s | Avg reasoning / completion tokens |
|---|---|---|---|---|---|---|---|---|
| mistral-small-2501 | **30** (5.0%) | 127 (21.2%) | 589 (98.2%) | 1 (0.2%) | 10 (1.7%) | 3.4 s / 5.8 s / 8.0 s / 9.8 s | 0 / 1228 | 0 / 90 |
| qwen-default | **18** (3.0%) | 29 (4.8%) | 590 (98.3%) | 2 (0.3%) | 8 (1.3%) | 13.3 s / 44.8 s / 95.7 s / 305 s | 44 (3.6%) | 309 / 363 |
| qwen-medium | 21 (3.5%) | 20 (3.3%) | 589 (98.2%) | 6 (1.0%) | 5 (0.8%) | 19.5 s / 56.0 s / 107.6 s / 212 s | 48 (3.9%) | 344 / 527 |
| qwen-low | 26 (4.3%) | 20 (3.3%) | 591 (98.5%) | 5 (0.8%) | 4 (0.7%) | 15.8 s / 35.2 s / 59.9 s / 82 s | 12 (1.0%) | 261 / 392 |
| qwen-nothink | 54 (9.0%) | 10 (1.7%) | 596 (99.3%) | 2 (0.3%) | 2 (0.3%) | 8.6 s / 19.4 s / 45.0 s / 84 s | 6 (0.5%) | 0 / 85 |

All 11 state-2 (auto-flagged) posts were judged spam by every config.

## False-positive overlap (good posts flagged spam)

- mistral 30, qwen-default 18: **15 in common, 15 mistral-only (rescued by Qwen), 3 qwen-only (new)** — posts 1110, 1523, 3501.
- Net effect of switching to qwen-default: 12 fewer real posts flagged (−40%).
- "Maybe" on good posts: mistral 127, qwen-default 29 (22 in common). Mistral is hesitant on ~1 in 5 good posts (they sit in state 3, visible, awaiting human review); Qwen is decisive.
- Bad posts missed (answered visible): both models miss ~1–2% — essentially the same posts.

## Does the existing production code handle a thinking LLM?

**The call pattern works** — no HTTP 400s, no protocol issues, identical verdict mapping, and
`qwen-default` (no extra params) is exactly what the current code sends. But two production gaps:

1. **Timeout.** `OPENAI_ARGS` in `openai_spamjudge.py` defaults to 60 s. 3.6% of qwen-default
   calls exceed 60 s (p99 95.7 s, max 305 s; qwen-low 1.0%, qwen-nothink 0.5%). A timeout raises
   → the post lands in **state 4 (Error)**, and the cron only picks up state 0, so it stays there
   (visible) until a human intervenes.
2. **Parse failures.** ~0.7% of thinking calls (9.4% nothink) return malformed JSON
   (`{"wanted": "yes", "yes"` etc.) → also state 4. In this run a single retry fixed **100%** of
   the 576 first-attempt failures, so a retry (or re-queuing state 4 posts) removes the problem.

The code also cannot *control* thinking effort (no `extra_body` support) — Qwen would always
think at default effort.

## Verdict

- **qwen-default is a net improvement for the no-false-positives priority**: 3.0% vs 5.0% good
  posts flagged, 4.8% vs 21.2% maybe-on-good, equal recall on verified spam. Cost: ~4× latency
  (p50 13.3 s vs 3.4 s), ~4× completion tokens, and the two production gaps above.
- **Thinking helps precision on good posts**: nothink has the best recall (99.3%) but 3× the
  false positives (9.0%). The effort knob (default/medium/low) moves quality little — default is
  best on FPs, low is the latency compromise (p95 35 s, only 1% over 60 s).
- **If adopting Qwen**, production needs: timeout 60 s → 300 s; retry on parse failure /
  re-queue state 4; optional `OPENAI_EXTRA_BODY` setting to pass `reasoning_effort` (openai
  1.61.1 supports `extra_body` on `chat.completions.create`).
- **If keeping mistral**, nothing needs to change.

## Pre-existing production bug (found during eval, both models affected)

Post 40775's creator user was deleted from the database. `DEFAULT_POST_PROMPT` renders
`{{post.creator}}`; with a missing user that raises `DoesNotExist` → the post lands in state 4
and is never retried. The prompt render should guard against a missing creator (e.g.
`post.creator.username if post.creator else '(unknown)'`).

## Files

- `run_eval.py` — eval runner (production call path, incremental JSONL, resume, retries)
- `rerun_errors.py` — retry failed posts with 429 backoff + parse-failure retries
- `analyze_llm.py` — analysis (prints the tables above)
- `sample_posts.json` / `sample_full.csv` — the 1228-post sample with production context
- `results_<config>.jsonl` — per-post verdicts, latency, token usage (final, error-free)
