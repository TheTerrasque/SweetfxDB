# laya as first-line forum spam filter — evaluation report

Date: 2026-09-19 · Branch: `laya-spam-prefilter` (from `v3.46` / `8af6bfe`)
Model: `convaiinnovations/laya` (Qwen3-0.6B RL) via http://127.0.0.1:8321, CUDA
Question: `Is `post` spam or advertising?` (type: noul)

## Data

Production DB (postgres-0, ns `database`, db `sweetfx`), table `forum_forumpost`:

| label | state | n |
|---|---|---|
| good (visible) | 1 | 2915 |
| bad (human-verified spam) | 5 | 2890 |
| bad (LLM-marked spam) | 2 | 11 |
| unsure | 3 | 17 |

Total scored: 5833 in 136 s ≈ **43 posts/s** (~23 ms/post).

Note: model sees at most ~319 tokens of state (max_len 512, head 192, right-truncation).

## Headline numbers

- **AUC = 0.919**
- Score medians: good **0.044** vs bad **0.888**
- Bad posts: 48.5% ≥ 0.9 · 35.3% in 0.3–0.9 · 16.2% < 0.3
- Good posts: 85.2% < 0.3 · 13.2% in 0.3–0.9 · 1.5% ≥ 0.9

| threshold | TP | FP | precision | recall | F1 |
|---|---|---|---|---|---|
| 0.20 | 2560 | 598 | 0.811 | 0.882 | 0.845 |
| 0.50 | 2212 | 286 | 0.886 | 0.762 | 0.819 |
| 0.80 | 1751 | 129 | 0.931 | 0.604 | 0.732 |
| 0.90 | 1406 | 44 | **0.970** | 0.485 | 0.646 |
| 0.95 | 1176 | 17 | 0.986 | 0.405 | 0.574 |

## What laya catches well

- Long-form SEO spam (median 958 chars; 96% contain URLs) → mostly ≥ 0.9
- Non-English SEO spam (Korean/German): 131/149 ≥ 0.9, avg 0.959
- Obvious off-topic advertising (casinos, drugs, supplements, paper-writing)

## What it misses (16.2% of bad score < 0.3)

- Short link-drop posts (`www.banana-anma.com` ×6, `youtu.be`, `mtlive1.com`, bare `<a href>` spam)
- Polite-sounding SEO ("Thank you for this insightful post!")
- On-topic-looking AI answers with links embedded
- 7 bare "Thank you" posts

Its "spam" concept ≈ *long off-topic advertising text*, not *link dropping*.

## False positives (44 good posts ≥ 0.9, 1.5%)

Legit users sharing preset/injector links (reshade.me, yadi.sk, drive.google.com, pastebin).
The model over-penalizes link sharing; legit link posts are the main FP class.

## Complementary heuristic

`len < 200 AND has URL`: catches 614/2901 bad but hits 206/2915 good (precision 0.75) —
ok as a review flag, not as auto-delete.
Combined `noul ≥ 0.9 OR short+URL`: catches 61.5% of bad, hits 8.0% of good, precision 0.884.

## Suggested use

1. **Auto-spam at noul ≥ 0.9**: catches ~half of all historical spam at 97% precision
   (44 FPs across 2915 good posts).
2. **Human review band 0.3–0.9**: another ~35% of spam, at the cost of ~13% of good posts.
3. **Remaining ~16%** (short link drops, polite spam) needs a different mechanism:
   URL heuristics, account age/post-rate, or the existing LLM pass.

## Caveats

- "good" = visible on site (human-approved), may include a little slipped-through spam.
- "bad" = 2890 human-verified + 11 LLM-marked.
- Historical data only; future spam waves (new domains, new languages) may shift scores.

## Files

- `posts.csv` — raw export (id, state, text)
- `results.json` — per-post noul + confidence
- `scores.csv` — id, state, noul, label
- `run_eval.py` / `analyze.py` — reproducible pipeline

## Production integration (branch laya-spam-prefilter)

Implemented as a first tier inside the existing `process_forum_spam` cronjob:

- `sweetfx_database/forum/laya_prefilter.py` — `LayaPrefilter.decide(post)`:
  - baseline question on the raw post; score >= `SFX_LAYA_SPAM_THRESHOLD` (0.99)
    auto-hides the post (state 2, same as an LLM "yes", including the
    permission-stripping check) and skips the LLM
  - **allowlist veto**: if every URL in the post resolves to an allowed domain
    (34 data-driven domains, default in the module), the post is NOT auto-hidden
    even at 0.99+ — this rescued 5 of the 10 historical FPs
  - optional `SFX_LAYA_PASS_THRESHOLD`: scores below it mark the post visible
    without an LLM call (default off)
  - optional `SFX_LAYA_REQUIRE_MARKER_CONFIRM`: second call with URLs replaced
    by [ok:]/[?:] markers must agree before auto-hide (default off)
  - laya unreachable/disabled -> every post falls through to the LLM (never breaks the pipeline)
- `process_forum_spam` gained `--laya-url` (overrides the setting for manual runs)
- settings: `SFX_LAYA_BASE_URL` (empty = disabled), `SFX_LAYA_SPAM_THRESHOLD`,
  `SFX_LAYA_PASS_THRESHOLD`, `SFX_LAYA_REQUIRE_MARKER_CONFIRM`,
  `SFX_LAYA_ALLOWED_DOMAINS` (comma-separated)
- `openai_spamjudge.judge_post` refactored: the spam-permission check moved to
  `check_spam_permissions(post)` so both tiers share it
- unit tests in `sweetfx_database/forum/tests.py`; live smoke test against
  127.0.0.1:8321 on 2026-09-19: casino SEO auto-hidden (42ms), legit
  microsoft.com link post vetoed, plain post and link-drop spam fell through
