"""m17n parity battery: our pure-rules mode vs the real m17n engine.

Feeds keystrokes to m17n-input-test (ne/rom-translit) and asserts
committed+preedit equals our dictionary=False output. This proves the
rules core is m17n-faithful; the dictionary layer is purely additive.

Skipped where m17n is not installed (e.g. Windows CI).
"""
import os
import re
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.nepali_transl import transliterate

M17N_BIN = shutil.which("m17n-input-test")
DUMMY = "m17n-parity"

BATTERY = [
    # vowels
    "a", "aa", "A", "i", "ii", "I", "ee", "u", "uu", "U", "oo",
    "rri", "rree", "e", "ai", "o", "au", "OM", "AUM",
    # consonants
    "k", "q", "c", "kh", "g", "gh", "ng",
    "ch", "chh", "j", "z", "jh", "yn",
    "T", "t/", "Th", "th/", "D", "d/", "Dh", "dh/", "n/",
    "t", "th", "d", "dh", "n",
    "p", "f", "ph", "b", "bh", "m",
    "y", "r", "l", "v", "w",
    "sh", "Sh", "shh", "s", "h",
    "ks", "ksh", "x", "gy", "gyn",
    # matras on ka
    "ka", "kaa", "ki", "kii", "ku", "kuu", "ke", "kai", "ko", "kau",
    "kri", "kha", "khaa",
    # words (pure rules only; NOTE: bare "tr" shows m17n's pending
    # preedit without halant — "tra" proves both compose identically;
    # jna/R/N/Nepal/~ are intentional extensions, tested separately)
    "namaste", "kathmandu", "hello", "kasto", "chha", "tra",
    "shra", "khaana", "ma", "sanga", "garchhu",
    # signs + digits + punct
    "aM", "a*", "aH", "0", "5", "9", ".", "..", "~a",
    "T", "Dh",
]


def _m17n_output(word):
    args = ["m17n-input-test", "--language", "ne", "--name", "rom-translit"]
    for ch in word:
        args += ["-k", ch]
    args += ["--commit", DUMMY, "--preedit", DUMMY]
    p = subprocess.run(args, capture_output=True, text=True, timeout=30)
    out = p.stdout + p.stderr
    com = re.search(r"committed does not match\. Expected '.*?', got '(.*)'\.",
                    out)
    pres = re.findall(r"preedit does not match\. Expected '.*?', got '(.*)'\.",
                      out)
    return (com.group(1) if com else "") + (pres[-1] if pres else "")


def test_m17n_parity():
    if not M17N_BIN:
        print("  (skip test_m17n_parity: m17n-input-test not installed)")
        return
    ours = transliterate("probe", dictionary=False)  # warmup
    bad = []
    for word in BATTERY:
        try:
            got = _m17n_output(word)
        except subprocess.TimeoutExpired:
            bad.append((word, "TIMEOUT", ""))
            continue
        want = transliterate(word, dictionary=False)
        if got != want:
            bad.append((word, got, want))
    assert not bad, f"{len(bad)} mismatches: {bad[:8]}"


def test_intentional_extensions():
    """Where we deliberately go beyond mim (documented, tested here).

    - jn -> ज्ञ (mim: ज्न; ours accepts the common shorthand)
    - x -> क्स (mim: no x key at all)
    - R/N/M at word start -> र/न/म consonants (mim leaves them literal)
    - lone ~ -> । (mim holds it pending for ~a)
    """
    assert transliterate("jn", dictionary=False) == "ज्ञ"
    assert transliterate("x", dictionary=False) == "क्स"
    assert transliterate("R", dictionary=False) == "र"
    assert transliterate("Nepal", dictionary=False) == "नेपल"
    assert transliterate("~", dictionary=False) == "।"


def run_all():
    try:
        test_m17n_parity()
        print("  PASS test_m17n_parity")
    except AssertionError as e:
        print(f"  FAIL test_m17n_parity: {e}")
        return False
    try:
        test_intentional_extensions()
        print("  PASS test_intentional_extensions")
        return True
    except AssertionError as e:
        print(f"  FAIL test_intentional_extensions: {e}")
        return False


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
