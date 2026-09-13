"""Tests for the IBus engine (no daemon/gi needed).

NepaliEngineBase holds all typing logic framework-free; the IBus
subclass is a thin I/O layer. We also verify the component XML parses
and names the right engine/language.
"""
import os
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.nepali_transl import get_transliterator


def _logic():
    import importlib.util
    import importlib.machinery
    path = os.path.join(os.path.dirname(__file__), "..", "ibus",
                        "ibus-engine-nepali-transl")
    loader = importlib.machinery.SourceFileLoader("ibus_engine", path)
    spec = importlib.util.spec_from_loader(loader.name, loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod.NepaliEngineBase(get_transliterator())


def test_typing_flow():
    eng = _logic()
    pre, cands = eng.handle_char("n")
    assert pre == "न", pre
    pre, cands = eng.handle_char("a")
    assert pre == "न", (pre, cands)
    pre, cands = eng.handle_char("m")
    assert eng.current_top() == "नाम", eng.current_top()  # hand dict
    assert eng._buf == "nam"


def test_backspace_escape():
    eng = _logic()
    eng.handle_char("k")
    pre, cands, consumed = eng.handle_backspace()
    assert consumed and pre == ""
    _, _, consumed = eng.handle_backspace()
    assert not consumed
    eng.handle_char("a")
    assert eng.handle_escape() is True
    assert eng.handle_escape() is False


def test_candidates_flow_to_lookup():
    eng = _logic()
    for ch in "kathmandu":
        pre, cands = eng.handle_char(ch)
    assert pre == "काठमाडौं", pre
    assert cands and cands[0] == "काठमाडौं", cands


def test_component_xml():
    path = os.path.join(os.path.dirname(__file__), "..", "ibus",
                        "nepali_translit.xml")
    tree = ET.parse(path)
    root = tree.getroot()
    assert root.findtext("name") == "org.freedesktop.IBus.NepaliTranslit"
    eng = root.find("engines/engine")
    assert eng.findtext("name") == "nepali-translit"
    assert eng.findtext("language") == "ne"
    assert eng.findtext("layout") == "us"
    assert os.path.basename(root.findtext("exec")) == \
        "ibus-engine-nepali-transl"


def run_all():
    tests = [test_typing_flow, test_backspace_escape,
             test_candidates_flow_to_lookup, test_component_xml]
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
