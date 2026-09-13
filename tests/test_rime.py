"""Tests for the Rime schema export (no Rime install needed).

Regenerates into a temp dir and validates structure: headers, row
format (Devanagari TAB ascii-code), hand-before-auto ordering.
"""
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _export_tmp():
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))
    import export_rime
    tmp = tempfile.mkdtemp(prefix="rime-test-")
    rows = export_rime.export(tmp)
    return tmp, rows


def test_rime_dict_format():
    tmp, rows = _export_tmp()
    assert len(rows) > 6000, len(rows)
    path = os.path.join(tmp, "nepali_translit.dict.yaml")
    text = open(path, encoding="utf-8").read()
    assert "name: nepali_translit" in text
    assert "sort: original" in text
    body = text.split("...\n", 1)[1]
    lines = [l for l in body.splitlines() if l.strip()]
    assert len(lines) == len(rows)
    import unicodedata
    for line in lines:
        form, code = line.split("\t")
        assert form and all(
            unicodedata.name(c, "").startswith("DEVANAGARI")
            for c in form), line
        assert code.isascii() and code.isalpha() and code.islower(), line
    # hand entries come first: kathmandu precedes any auto-only key
    forms = [l.split("\t")[0] for l in lines]
    assert forms.index("काठमाडौं") < forms.index("काकी")


def test_rime_schema_present():
    tmp, _ = _export_tmp()
    text = open(os.path.join(tmp, "nepali_translit.schema.yaml"),
                encoding="utf-8").read()
    assert "schema_id: nepali_translit" in text
    assert "dictionary: nepali_translit" in text
    assert "table_translator" in text


def run_all():
    tests = [test_rime_dict_format, test_rime_schema_present]
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
