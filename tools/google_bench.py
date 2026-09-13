"""Benchmark OUR engine against Google Input Tools + emit a review file.

Compares transliterate(key) with Google's top candidate over a wordlist.
Writes tools/google_review.tsv with disagreements for HUMAN review — nothing
is imported automatically (see module docstring in core/google_backend.py
for the fair-use note).

Usage:
    python3 tools/google_bench.py [--limit 300] [--words w1,w2,...]
    python3 tools/google_bench.py --from-auto 2000   # sample auto keys

Cache: tools/.google_cache.jsonl (gitignored) so re-runs don't re-query.
"""
import argparse
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.nepali_transl import transliterate, get_transliterator
from core.dictionary import WORD_CORRECTIONS
from core.google_backend import google_transliterate

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, ".google_cache.jsonl")


def load_cache():
    cache = {}
    if os.path.exists(CACHE):
        with open(CACHE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        r = json.loads(line)
                        cache[r["q"]] = r["cands"]
                    except (ValueError, KeyError):
                        pass
    return cache


def save_cache_row(q, cands):
    with open(CACHE, "a", encoding="utf-8") as f:
        f.write(json.dumps({"q": q, "cands": cands},
                           ensure_ascii=False) + "\n")


def query_one(word, num=3):
    """Single-word query (one request)."""
    res = google_transliterate(word, num=num)
    return res.get(word, [])


def batch_query(words, cache, pause=0.4, batch=12):
    """Query Google; returns {word: [cands]}.

    The endpoint transliterates a multi-word query as ONE sentence, so we
    align whitespace-split outputs back to inputs and verify counts; any
    batch that doesn't align 1:1 is re-queried word by word.
    """
    out, todo = {}, [w for w in words if w not in cache]
    for w in words:
        if w in cache:
            out[w] = cache[w]

    def _store(w, cands):
        out[w] = cands
        save_cache_row(w, cands)

    for i in range(0, len(todo), batch):
        chunk = todo[i:i + batch]
        try:
            res = google_transliterate(" ".join(chunk), num=1)
            sent = (res.get(" ".join(chunk), []) or [""])[0]
            aligned = sent.split(" ")
        except Exception as e:
            print(f"  [warn] batch failed ({e}); stopping", file=sys.stderr)
            break
        if len(aligned) == len(chunk):
            for w, t in zip(chunk, aligned):
                _store(w, [t])
        else:
            for w in chunk:  # fall back to individual queries
                try:
                    _store(w, query_one(w))
                except Exception as e:
                    print(f"  [warn] {w}: {e}", file=sys.stderr)
                    _store(w, [])
                time.sleep(pause)
        time.sleep(pause)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--words", default="")
    ap.add_argument("--from-auto", type=int, default=0)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)

    if args.words:
        words = [w.strip().lower() for w in args.words.split(",") if w.strip()]
    elif args.from_auto:
        from core.words_auto import AUTO_CORRECTIONS
        pool = sorted(AUTO_CORRECTIONS)
        rnd = random.Random(args.seed)
        words = rnd.sample(pool, min(args.from_auto, len(pool)))
    else:
        words = sorted(WORD_CORRECTIONS)[:args.limit]

    print(f"benchmarking {len(words)} words (cache: {CACHE})")
    cache = load_cache()
    results = batch_query(words, cache)

    agree = disagree = noanswer = 0
    review = []
    for w in words:
        ours = transliterate(w)
        cands = results.get(w, [])
        if not cands:
            noanswer += 1
            continue
        if ours == cands[0]:
            agree += 1
        else:
            disagree += 1
            review.append((w, ours, cands[0], "|".join(cands[1:3])))

    print(f"agree={agree} disagree={disagree} noanswer={noanswer}")

    # Enrich disagreements with Google's full candidate list (top-5) so the
    # reviewer can see whether OUR form appears as Google's #2/#3.
    if review:
        print("fetching full candidates for disagreements...")
        cache = load_cache()
        enriched = []
        for w, ours, gtop, _ in review:
            cands = cache.get(w, [])
            if len(cands) < 2:
                try:
                    cands = query_one(w, num=5)
                    save_cache_row(w, cands)
                except Exception as e:
                    print(f"  [warn] {w}: {e}", file=sys.stderr)
                time.sleep(0.4)
            enriched.append((w, ours, cands[0] if cands else "",
                             "|".join(cands[1:4])))
        review = enriched
    if review:
        path = os.path.join(HERE, "google_review.tsv")
        with open(path, "w", encoding="utf-8") as f:
            f.write("roman\tours\tgoogle_top\tgoogle_alts\n")
            for row in review:
                f.write("\t".join(row) + "\n")
        print(f"wrote {path} ({len(review)} rows for human review)")
        for row in review[:15]:
            print(f"  {row[0]:18} ours={row[1]:14} google={row[2]}")


if __name__ == "__main__":
    raise SystemExit(main())
