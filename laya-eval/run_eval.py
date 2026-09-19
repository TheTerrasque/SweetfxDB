"""Run laya spam prediction over the labeled sweetfx forum posts.

Reads posts.csv (id, state, text), calls the laya bulk endpoint in chunks of
256, and writes results.json with per-post noul scores + label.
"""
import csv
import json
import sys
import time
import urllib.request

csv.field_size_limit(sys.maxsize)

URL = "http://127.0.0.1:8321/predict/bulk"
INSTRUCTIONS = "Is `post` spam or advertising?"
QUESTIONS = {"spam": {"type": "noul", "instructions": INSTRUCTIONS}}
CHUNK = 256

def main():
    rows = []
    with open("posts.csv", newline="", encoding="utf-8") as f:
        for r in csv.reader(f):
            if len(r) == 3:
                rows.append((int(r[0]), int(r[1]), r[2]))
    print(f"loaded {len(rows)} posts", flush=True)

    results = {}
    t_start = time.time()
    for i in range(0, len(rows), CHUNK):
        chunk = rows[i:i + CHUNK]
        payload = json.dumps({
            "states": [{"post": t} for _, _, t in chunk],
            "questions": QUESTIONS,
        }).encode("utf-8")
        req = urllib.request.Request(URL, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=600) as resp:
            data = json.loads(resp.read())
        for (pid, state, _), res in zip(chunk, data["results"]):
            results[pid] = {
                "state": state,
                "noul": res["answers"]["spam"]["noul"],
                "confidence": res["answers"]["spam"]["confidence"],
            }
        elapsed = time.time() - t_start
        print(f"{i + len(chunk)}/{len(rows)}  ({elapsed:.0f}s, {len(chunk) * (i + 1) / elapsed:.0f} posts/s)", flush=True)

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False)
    print(f"done in {time.time() - t_start:.0f}s -> results.json")

if __name__ == "__main__":
    main()
