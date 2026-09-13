"""Honest held-out evaluation — answers "99.5% on what?".

Seeded 50/50 split of pair rows: the auto dictionary is rebuilt from
half A ONLY, then measured on never-seen half B. Reports:

  phonetic-only on B ......... pure rules, no dictionary
  hand + auto(A) on B ........ THE honest generalization number
  shipped dict on B .......... reference (mildly leaky: shipped dict saw
                               all rows during import; shown for contrast)
  shipped dict on A .......... train recall (the old 99.5%-style number)

Usage:
    python3 tools/eval_split.py [/tmp/nep_valid.json /tmp/nep_test.json]
    python3 tools/eval_split.py --seed 123 [...]
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import core.nepali_transl as NTM
from import_pairs import load_rows, build_auto


def accuracy(tr, rows, use_dict):
    hit = 0
    for r in rows:
        key = r["english word"].strip().lower()
        if use_dict:
            got = tr.transliterate(key)
        else:
            got = tr._transliterate_word(key, use_dict=False)
        if got == r["native word"]:
            hit += 1
    return hit, len(rows)


def main(argv):
    toks = argv[1:]
    seed = 42
    only_source = None
    paths = []
    skip_next = False
    for i, a in enumerate(toks):
        if skip_next:
            skip_next = False
            continue
        if a == "--seed":
            seed = int(toks[i + 1])
            skip_next = True
        elif a.startswith("--seed="):
            seed = int(a.split("=", 1)[1])
        elif a == "--source":
            only_source = toks[i + 1]
            skip_next = True
        elif a.startswith("--source="):
            only_source = a.split("=", 1)[1]
        elif not a.startswith("--"):
            paths.append(a)
    paths = paths or ["/tmp/nep_valid.json", "/tmp/nep_test.json"]
    # Isolate the user lexicon: a developer's learned words must not leak
    # into "honest" numbers (or pollute their real lexicon file).
    import tempfile
    os.environ["NEPALI_TRANSL_HOME"] = tempfile.mkdtemp(prefix="eval-split-")
    rows = load_rows(paths)
    if only_source:
        rows = [r for r in rows if r.get("source") == only_source]
        print(f"filtered to source={only_source}: {len(rows)} rows")
    rnd = random.Random(seed)
    rnd.shuffle(rows)
    half = len(rows) // 2
    A, B = rows[:half], rows[half:]
    print(f"total={len(rows)} train_half={len(A)} heldout_half={len(B)} seed={seed}")

    autoA, statsA = build_auto(A)
    print(f"auto dict from half A: {len(autoA)} entries")

    real_auto = NTM.AUTO_CORRECTIONS
    try:
        # 1. phonetic-only on held-out B (no dict at all)
        NTM.AUTO_CORRECTIONS = {}
        tr_plain = NTM.NepaliTransliterator.__new__(NTM.NepaliTransliterator)
        NTM.NepaliTransliterator.__init__(tr_plain)
        # __init__ reads patched (empty) AUTO for the pool; force phonetic:
        hp, n = accuracy(tr_plain, B, use_dict=False)
        # 2. honest number: hand + auto(A) on held-out B
        NTM.AUTO_CORRECTIONS = {k: v[0] for k, v in autoA.items()}
        tr_a = NTM.NepaliTransliterator()
        ha, n = accuracy(tr_a, B, use_dict=True)
    finally:
        NTM.AUTO_CORRECTIONS = real_auto

    # 3/4. shipped dict (leaky reference): fresh instance, global restored
    tr_ship = NTM.NepaliTransliterator()
    sa, _ = accuracy(tr_ship, B, use_dict=True)
    sb, m = accuracy(tr_ship, A, use_dict=True)

    def pct(h, t):
        return f"{h}/{t} = {100.0 * h / t:.1f}%"

    print(f"phonetic-only on held-out B .... {pct(hp, n)}")
    print(f"hand + auto(A) on held-out B ... {pct(ha, n)}  <-- HONEST NUMBER")
    print(f"shipped dict on held-out B ..... {pct(sa, n)}  (leaky ref)")
    print(f"shipped dict on train half A ... {pct(sb, m)}  (train recall)")


if __name__ == "__main__":
    main(sys.argv)
