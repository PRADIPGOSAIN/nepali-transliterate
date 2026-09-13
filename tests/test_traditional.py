"""Tests for traditional keyboard layout mode."""
import ast
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.traditional import TRAD_MAP, traditional_type, LAYOUT_NAME
from core.nepali_transl import transliterate

MIM_PATH = "/usr/share/m17n/ne-trad.mim"


def _unescape_key(s: str) -> str:
    """Unescape mim key escapes (keys are ASCII + \\ and \")."""
    return s.replace("\\\\", "\\").replace('\\"', '"')


def _mim_table():
    """Extract the (trans ...) mapping from the installed mim file."""
    with open(MIM_PATH, encoding="utf-8") as f:
        text = f.read()
    table = {}
    for a, b in re.findall(r'\("((?:[^"\\]|\\.)*)" \?(.)\)', text):
        table[_unescape_key(a)] = b
    for a, b in re.findall(r'\("((?:[^"\\]|\\.)*)" "((?:[^"\\]|\\.)*)"\)', text):
        table[_unescape_key(a)] = b
    return table


def test_parity_with_mim():
    if not os.path.exists(MIM_PATH):
        print("  (skip test_parity_with_mim: m17n not installed here)")
        return
    mim = _mim_table()
    assert len(mim) == len(TRAD_MAP) == 94, (len(mim), len(TRAD_MAP))
    for k, v in mim.items():
        assert TRAD_MAP.get(k) == v, (k, repr(v), repr(TRAD_MAP.get(k)))


def test_home_row():
    # physical home row keys -> traditional chars
    assert traditional_type("asdf") == "बकमा"  # a=ब s=क d=म f=ा
    assert traditional_type("a") == "ब"
    assert traditional_type("s") == "क"
    assert traditional_type("k") == "प"
    assert traditional_type("f") == "ा"
    assert traditional_type("l") == "ि"


def test_shift_layer():
    assert traditional_type("A") == "आ"
    assert traditional_type("L") == "ी"
    assert traditional_type("!") == "ज्ञ"
    assert traditional_type("Q") == "त्त"


def test_digits_punct():
    assert traditional_type("123") == "१२३"
    assert traditional_type(".") == "।"
    assert traditional_type("q") == "त्र"
    assert traditional_type("[") == "र्"


def test_passthrough():
    assert traditional_type(" ") == " "
    assert traditional_type("\n") == "\n"
    assert traditional_type("a b") == "ब द"  # a=ब b=द


def test_modes_differ():
    # same keystrokes, different modes -> different output (the point of modes)
    assert transliterate("k", mode="roman") == "क"
    assert transliterate("k", mode="traditional") == "प"
    assert LAYOUT_NAME == "traditional-mpp"


def test_no_network_imports_in_core():
    """Independence guarantee: core engine must stay offline-capable.

    Only google_backend.py may touch the network (explicitly online).
    """
    import pathlib
    net_mods = ("urllib", "socket", "http.client", "requests", "httpx")
    offenders = []
    for path in pathlib.Path("core").glob("*.py"):
        if path.name == "google_backend.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom):
                mods = [node.module or ""]
            else:
                continue
            if any(m.split(".")[0] in net_mods for m in mods):
                offenders.append((str(path), mods))
    assert not offenders, offenders


def run_all():
    tests = [test_parity_with_mim, test_home_row, test_shift_layer,
             test_digits_punct, test_passthrough, test_modes_differ,
             test_no_network_imports_in_core]
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
