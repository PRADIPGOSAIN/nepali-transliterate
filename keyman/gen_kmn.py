"""Generate a Keyman keyboard source (.kmn) from the nepali-transl mapping.

Keyman (keyman.com, free + open source) is the system-wide input-method
framework for Windows / macOS / Linux / Android / iOS / Web.
This script emits `nepali_translit.kmn` carrying the SAME phonetic mapping
as ne-rom-translit.mim, so Windows/macOS/mobile users type exactly like
the Linux m17n/fcitx5 setup.

Usage:
    python3 keyman/gen_kmn.py            # writes keyman/nepali_translit.kmn
    python3 keyman/gen_kmn.py --check    # verify all mappings covered

Build the installable package afterwards:
    1. Install Keyman Developer (free) from keyman.com/developer
    2. Open nepali_translit.kmn -> Start Compiler -> Build .kmp
    3. Share the .kmp: double-click installs the keyboard on Windows.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.nepali_transl import (
    CONSONANT_MAP,
    INDEPENDENT_VOWELS,
    DEPENDENT_VOWELS,
    ANUSWAR,
    PUNNA_VIRAM,
    NUMBERS,
    HALANT,
    HALANT_ZWNJ,
    ZWNJ_HALANT_ZWJ,
)

HERE = os.path.dirname(os.path.abspath(__file__))


def kmn_escape(s: str) -> str:
    return s.replace("'", "''")


def build_kmn() -> str:
    L = []
    A = L.append
    A("c Nepali Transliterate keyboard — generated from nepali-transl mapping")
    A("c Source project: nepali-transl engine by Pradip Gosain (GPL-2.0-or-later)")
    A("c License: GPL-2.0-or-later")
    A("")
    A("store(&VERSION) '10.0'")
    A("store(&NAME) 'Nepali Transliterate'")
    A("store(&COPYRIGHT) 'GPL-2.0-or-later'")
    A("store(&MESSAGE) 'Romanized Nepali: type namaste -> \\U0928\\U092E\\U0938\\U094D\\U0924\\U0947'")
    A("store(&TARGETS) 'any'")
    A("store(&LANGUAGE) 'ne'")
    A("")
    # --- consonants that can take a matra (single output char only) ---
    matra_cons = sorted({v for v in CONSONANT_MAP.values() if len(v) == 1})
    A("c Consonants accepting matras")
    A("store(consonant) " + " ".join(f"'{kmn_escape(c)}'" for c in matra_cons))
    # --- vowel keys + parallel matra outputs (longest first for any() match) ---
    vkeys = sorted(DEPENDENT_VOWELS.keys(), key=len, reverse=True)
    A("c Vowel keys (any() longest-match) and their matras")
    A("store(vowelkey) " + " ".join(f"'{kmn_escape(k)}'" for k in vkeys))
    A("store(vowelmat) " + " ".join(f"'{kmn_escape(DEPENDENT_VOWELS[k])}'" for k in vkeys))
    A("")
    A("begin Unicode > use(main)")
    A("")
    A("group(main) using keys")
    A("")
    A("c --- 1. multi-char consonant clusters, longest first ---")
    for k in sorted(CONSONANT_MAP.keys(), key=len, reverse=True):
        if len(k) > 1:
            A(f"  + '{kmn_escape(k)}' > '{kmn_escape(CONSONANT_MAP[k])}'")
    A("")
    A("c --- 2. consonant + vowel -> consonant + matra ---")
    A("  + any(consonant) + any(vowelkey) > index(vowelmat, 2)")
    A("")
    A("c --- 3. single consonants ---")
    for k in sorted(CONSONANT_MAP.keys(), key=len, reverse=True):
        if len(k) == 1:
            A(f"  + '{kmn_escape(k)}' > '{kmn_escape(CONSONANT_MAP[k])}'")
    A("")
    A("c --- 4. standalone vowels ---")
    for k in sorted(INDEPENDENT_VOWELS.keys(), key=len, reverse=True):
        A(f"  + '{kmn_escape(k)}' > '{kmn_escape(INDEPENDENT_VOWELS[k])}'")
    A("")
    A("c --- 5. digits ---")
    for k in sorted(NUMBERS):
        A(f"  + '{kmn_escape(k)}' > '{kmn_escape(NUMBERS[k])}'")
    A("")
    A("c --- 6. punctuation / signs ---")
    A("c word-start M/N act as consonants (mirrors the Python engine)")
    A("  + nul + 'M' > 'म'")
    A("  + nul + 'N' > 'न'")
    A(f"  + '..' > '{kmn_escape(PUNNA_VIRAM['..'])}'")
    A(f"  + '.' > '{kmn_escape(PUNNA_VIRAM['.'])}'")
    A(f"  + '~a' > '{kmn_escape(PUNNA_VIRAM['~a'])}'")
    for k in sorted(ANUSWAR):
        A(f"  + '{kmn_escape(k)}' > '{kmn_escape(ANUSWAR[k])}'")
    A(f"  + '\\\\' > '{kmn_escape(HALANT_ZWNJ)}'")
    A(f"  + '|' > '{kmn_escape(ZWNJ_HALANT_ZWJ)}'")
    A(f"  + '~' > '{kmn_escape(PUNNA_VIRAM['~'])}'")
    A("")
    return "\n".join(L) + "\n"


def check_coverage() -> list:
    """Every mapping key must appear in the generated source."""
    src = build_kmn()
    missing = []
    for table in (CONSONANT_MAP, INDEPENDENT_VOWELS, NUMBERS):
        for k in table:
            if f"'{kmn_escape(k)}'" not in src:
                missing.append(k)
    return missing


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    if args.check:
        missing = check_coverage()
        if missing:
            print("MISSING:", missing)
            return 1
        print(f"coverage OK: all mapping keys present")
        return 0
    out = os.path.join(HERE, "nepali_translit.kmn")
    with open(out, "w", encoding="utf-8") as f:
        f.write(build_kmn())
    print(f"wrote {out} ({os.path.getsize(out)} bytes)")


if __name__ == "__main__":
    raise SystemExit(main())
