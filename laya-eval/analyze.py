"""Analyze laya noul scores vs human labels: distributions, AUC, thresholds."""
import csv
import json
import sys
from collections import Counter

csv.field_size_limit(sys.maxsize)

with open("results.json", encoding="utf-8") as f:
    results = json.load(f)

rows = []
with open("posts.csv", newline="", encoding="utf-8") as f:
    for r in csv.reader(f):
        if len(r) == 3:
            pid, state, text = int(r[0]), int(r[1]), r[2]
            if str(pid) in results:
                rows.append((pid, state, text, results[str(pid)]["noul"]))

print(f"total: {len(rows)}")
print(Counter(s for _, s, _, _ in rows))

good = sorted(n for _, s, _, n in rows if s == 1)
bad = sorted(n for _, s, _, n in rows if s in (2, 5))
unsure = sorted(n for _, s, _, n in rows if s == 3)

def pct(xs, p):
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * p
    f = int(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)

def show(name, xs):
    print(f"{name:8s} n={len(xs):5d}  min={xs[0]:.3f} p05={pct(xs,.05):.3f} p25={pct(xs,.25):.3f} p50={pct(xs,.5):.3f} p75={pct(xs,.75):.3f} p95={pct(xs,.95):.3f} max={xs[-1]:.3f}")

show("good", good)
show("bad", bad)
show("unsure", unsure)

# AUC (Mann-Whitney)
def auc(pos, neg):
    # rank-based
    allv = [(v, 1) for v in pos] + [(v, 0) for v in neg]
    allv.sort()
    ranks = {}
    i = 0
    r = 0
    sum_pos = 0.0
    n = len(allv)
    # average ranks for ties
    i = 0
    while i < n:
        j = i
        while j + 1 < n and allv[j + 1][0] == allv[i][0]:
            j += 1
        avg_rank = (i + j) / 2 + 1
        for k in range(i, j + 1):
            if allv[k][1] == 1:
                sum_pos += avg_rank
        i = j + 1
    n_pos, n_neg = len(pos), len(neg)
    return (sum_pos - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg)

print(f"\nAUC (bad=positive): {auc(bad, good):.4f}")

# confusion at thresholds
print("\nthreshold  TP   FP   TN   FN  precision  recall   F1")
for t in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95]:
    tp = sum(1 for v in bad if v >= t)
    fp = sum(1 for v in good if v >= t)
    tn = len(good) - fp
    fn = len(bad) - tp
    prec = tp / (tp + fp) if tp + fp else 0
    rec = tp / (tp + fn) if tp + fn else 0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0
    print(f"{t:9.2f}  {tp:5d} {fp:5d} {tn:5d} {fn:5d}   {prec:.3f}    {rec:.3f}  {f1:.3f}")

# worst false positives: good posts with highest scores
print("\n=== 10 good posts with HIGHEST spam score (false positives at any threshold) ===")
g_sorted = sorted(((n, pid, text) for pid, s, text, n in rows if s == 1), reverse=True)
for n, pid, text in g_sorted[:10]:
    print(f"noul={n:.3f} id={pid}: {text[:150]!r}")

# worst false negatives: bad posts with lowest scores
print("\n=== 10 bad posts with LOWEST spam score (false negatives) ===")
b_sorted = sorted(((n, pid, text) for pid, s, text, n in rows if s in (2, 5)))
for n, pid, text in b_sorted[:10]:
    print(f"noul={n:.3f} id={pid}: {text[:150]!r}")

# how many bad posts are 'obvious' (noul >= 0.9) vs ambiguous
obv = sum(1 for v in bad if v >= 0.9)
amb = sum(1 for v in bad if 0.3 <= v < 0.9)
low = sum(1 for v in bad if v < 0.3)
print(f"\nbad posts: noul>=0.9: {obv} ({obv/len(bad):.1%}), 0.3-0.9: {amb} ({amb/len(bad):.1%}), <0.3: {low} ({low/len(bad):.1%})")
g_obv = sum(1 for v in good if v >= 0.9)
g_amb = sum(1 for v in good if 0.3 <= v < 0.9)
g_low = sum(1 for v in good if v < 0.3)
print(f"good posts: noul>=0.9: {g_obv} ({g_obv/len(good):.1%}), 0.3-0.9: {g_amb} ({g_amb/len(good):.1%}), <0.3: {g_low} ({g_low/len(good):.1%})")
