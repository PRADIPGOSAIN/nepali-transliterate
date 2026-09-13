"""Tests for direct keyboard-layout modes (romanized + traditional-kmn).

Parity is machine-checked against the vendored Keyman sources
(tools/reference/, MIT keymanapp/keyboards repo). m17n-traditional
parity lives in tests/test_traditional.py.
"""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.romanized_layout import ROMANIZED_MAP, romanized_type, LAYOUT_NAME as ROM_NAME
from core.traditional import (TRAD_KMN_MAP, traditional_kmn_type,
                              LAYOUT_KMN_NAME)
from core.nepali_transl import transliterate

REF_ROM = os.path.join(os.path.dirname(__file__), "..", "tools",
                       "reference", "nepali_romanized.kmn")
REF_TRAD = os.path.join(os.path.dirname(__file__), "..", "tools",
                        "reference", "nepali_traditional.kmn")


def _kmn_rules(path):
    """Parse `+ "X" > "Y"` / `> U+XXXX` rules; skip deadkeys + touch keys."""
    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().splitlines()
    table = {}
    for line in lines:
        # Keyman allows a lone backslash key written as "\" — normalize it
        # to the "\\" escape form before parsing (values untouched: the
        # dk() lines already use the double form).
        line = re.sub(r'^\+\s+"\\"(?=\s+>)', r'+ "\\\\"', line)
        # ... and single-quoted literals ('"') used for the double-quote key.
        m = re.match(r"""^\+\s+'((?:[^'\\]|\\.)*)'\s+>\s+(.+?)\s*$""", line)
        if m:
            key = m.group(1).replace("\\'", "'").replace("\\\\", "\\")
            val = m.group(2)
            if val.startswith("dk(") or val.startswith("[T_"):
                continue
            vm = re.match(r"""^'((?:[^'\\]|\\.)*)'$""", val)
            if vm:
                table[key] = vm.group(1).replace("\\'", "'").replace("\\\\", "\\")
                continue
            vm = re.match(r'^"((?:[^"\\]|\\.)*)"$', val)
            if vm:
                table[key] = vm.group(1).replace('\\"', '"').replace("\\\\", "\\")
                continue
            raise AssertionError(f"unparsed single-quoted rule: {line!r}")
        m = re.match(r'^\+\s+"((?:[^"\\]|\\.)*)"\s+>\s+(.+?)\s*$', line)
        if not m:
            continue
        key = m.group(1).replace("\\\\", "\\")
        val = m.group(2)
        if val.startswith("dk(") or val.startswith("[T_"):
            continue  # deadkey starter / touch-only extension
        vm = re.match(r'^"((?:[^"\\]|\\.)*)"$', val)
        if vm:
            table[key] = vm.group(1).replace("\\\\", "\\")
            continue
        um = re.match(r"^U\+([0-9A-Fa-f]+)$", val)
        if um:
            table[key] = chr(int(um.group(1), 16))
            continue
        raise AssertionError(f"unparsed rule: {line!r}")
    return table


def test_romanized_parity_with_kmn():
    if not os.path.exists(REF_ROM):
        print("  (skip: reference kmn absent)")
        return
    kmn = _kmn_rules(REF_ROM)
    assert len(kmn) == len(ROMANIZED_MAP), (len(kmn), len(ROMANIZED_MAP))
    for k, v in kmn.items():
        assert ROMANIZED_MAP.get(k) == v, (k, repr(v), repr(ROMANIZED_MAP.get(k)))


def test_tradkmn_parity_with_kmn():
    if not os.path.exists(REF_TRAD):
        print("  (skip: reference kmn absent)")
        return
    kmn = _kmn_rules(REF_TRAD)
    assert len(kmn) == len(TRAD_KMN_MAP), (len(kmn), len(TRAD_KMN_MAP))
    for k, v in kmn.items():
        assert TRAD_KMN_MAP.get(k) == v, (k, repr(v), repr(TRAD_KMN_MAP.get(k)))


def test_romanized_anchors():
    assert romanized_type("k") == "क"
    assert romanized_type("a") == "ा"
    assert romanized_type("A") == "आ"
    assert romanized_type("K") == "ख"
    assert romanized_type("123") == "१२३"
    assert romanized_type("/") == "्"
    assert romanized_type("\\") == "ॐ"
    assert ROM_NAME == "romanized-mpp"


def test_tradkmn_anchors():
    assert traditional_kmn_type("S") == "क्"   # classic has ङ्क here
    assert traditional_kmn_type("m") == "‌"   # ZWNJ, classic has ः
    assert traditional_kmn_type("[") == "ृ"   # classic has र्
    assert traditional_kmn_type("D") == "म्"  # classic has ङ्ग
    assert LAYOUT_KMN_NAME == "traditional-kmn-v1"


def test_all_four_modes():
    assert transliterate("namaste", mode="roman") == "नमस्ते"
    assert transliterate("k", mode="traditional") == "प"
    assert transliterate("S", mode="traditional-kmn") == "क्"
    assert transliterate("k", mode="romanized") == "क"
    try:
        transliterate("x", mode="bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("bogus mode should raise")


def test_om_word_start():
    assert transliterate("om") == "ॐ"
    assert transliterate("aum") == "ॐ"
    assert transliterate("omkar") == "ॐकर"
    # mid-word om stays o+m (sombar = सोमबार, not सॐबार)
    assert transliterate("sombar") == "सोमबार"


def run_all():
    tests = [test_romanized_parity_with_kmn, test_tradkmn_parity_with_kmn,
             test_romanized_anchors, test_tradkmn_anchors,
             test_all_four_modes, test_om_word_start]
    passed, failed = 0, 0
    for fn in tests:
        try:
            fn()
            print(f"  PASS {fn.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL {fn.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
