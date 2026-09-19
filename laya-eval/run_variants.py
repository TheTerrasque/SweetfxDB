"""Test question/state variants for the laya spam prefilter.

Variants:
  v1: baseline question + acceptable-domain list in the instructions
  v2: URLs in the post replaced with [ok:domain] / [?:domain] markers
  v3: explicit spam definition (incl. link dropping) + acceptable-domain list

All variants use the same 5833 labeled posts and the same laya server.
"""
import csv
import json
import re
import sys
import time
import urllib.request

csv.field_size_limit(sys.maxsize)

LAYA_URL = "http://127.0.0.1:8321"
BATCH = 256

# Data-driven allowlist: domains that legit (state-1) users use and
# spammers (state 2/5) barely use (good>=2, bad<=1, from the domain census).
ALLOWLIST = [
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
ALLOWSET = set(ALLOWLIST)

BASE_Q = "Is `post` spam or advertising?"
LIST_TXT = ", ".join(ALLOWLIST)

V1_Q = f"Is `post` spam or advertising? Links to these domains are acceptable: {LIST_TXT}"
V2_Q = ("Is `post` spam or advertising? "
        "[ok:X] marks a link to the trusted domain X. "
        "[?:X] marks a link to an untrusted domain X.")
V3_Q = (f"Is `post` spam? Spam includes off-topic advertising, promotion of external "
        f"services, or dropping links to untrusted domains. "
        f"Links to these domains are acceptable: {LIST_TXT}")

# URL extraction: http(s)://, www., <a href="...">
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


def domain_of(raw: str) -> str | None:
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
    # strip path junk that slipped in
    if not all(re.fullmatch(r"[a-z0-9\-]+", p) for p in parts):
        return None
    # registrable-ish: last two labels, or three for co.uk style
    if len(parts) >= 3 and parts[-2] in ("co", "com", "org", "net", "gov", "ac"):
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def in_allowlist(domain: str) -> bool:
    for a in ALLOWSET:
        if domain == a or domain.endswith("." + a) or a.endswith("." + domain):
            return True
    return False


def preprocess(text: str) -> str:
    """Replace URLs with [ok:domain] / [?:domain] markers."""
    def repl(m):
        raw = m.group(1) or m.group(2)
        d = domain_of(raw)
        if d is None:
            return m.group(0)
        return "[ok:%s]" % d if in_allowlist(d) else "[?:%s]" % d
    return URL_RE.sub(repl, text)


def make_variant(name):
    if name == "v1":
        return lambda t: ({"post": t}, V1_Q)
    if name == "v2":
        return lambda t: ({"post": preprocess(t)}, V2_Q)
    if name == "v3":
        return lambda t: ({"post": t}, V3_Q)
    raise ValueError(name)


def main():
    variant = sys.argv[1]
    out = sys.argv[2]
    make = make_variant(variant)

    rows = []
    with open("posts.csv", newline="", encoding="utf-8") as f:
        for r in csv.reader(f):
            if len(r) == 3:
                rows.append((int(r[0]), int(r[1]), r[2]))

    results = {}
    t0 = time.time()
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        q = make(batch[0][2])[1]  # question is identical for all posts
        payload = json.dumps({
            "states": [make(t)[0] for _, _, t in batch],
            "questions": {"spam": {"type": "noul", "instructions": q}},
        }).encode("utf-8")
        req = urllib.request.Request(
            LAYA_URL + "/predict/bulk", data=payload,
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for (pid, state, _), res in zip(batch, data["results"]):
            results[str(pid)] = {"state": state, "noul": res["answers"]["spam"]["noul"]}
        if (i // BATCH) % 4 == 0:
            el = time.time() - t0
            print(f"  batch {i//BATCH+1}/{(len(rows)-1)//BATCH+1} "
                  f"({el:.0f}s, {i/BATCH*256/el:.0f}/s)", flush=True)

    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f)
    print(f"done: {len(results)} posts in {time.time()-t0:.0f}s -> {out}")


if __name__ == "__main__":
    main()
