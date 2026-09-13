"""Tests for the Keyman keyboard generator (no Keyman install needed).

Validates the generated .kmn covers every mapping and that the package
project files are well-formed XML. (Full kmc compilation is done
manually: see keyman/README.)
"""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from keyman.gen_kmn import build_kmn, check_coverage


def test_kmn_coverage():
    assert check_coverage() == []


def test_kmn_structure():
    src = build_kmn()
    assert "store(&VERSION)" in src
    assert "store(&KEYBOARDVERSION)" in src
    assert "begin Unicode > use(main)" in src
    assert "group(main) using keys" in src
    # combo rules for a cluster + matra sanity
    assert "+ 'ksh' > 'क्ष'" in src
    assert "+ 'k' 'aa' > 'का'" in src
    # no empty-string outputs (kmc rejects those)
    assert "> ''" not in src


def test_package_files_valid_xml():
    base = os.path.join(os.path.dirname(__file__), "..", "keyman", "package")
    for name in ("nepali_translit.kpj", "nepali_translit.kps"):
        path = os.path.join(base, name)
        assert os.path.exists(path), path
        ET.parse(path)  # raises on malformed XML


def run_all():
    tests = [test_kmn_coverage, test_kmn_structure,
             test_package_files_valid_xml]
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
