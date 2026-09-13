"""Tests for nepali-transl engine."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.nepali_transl import transliterate, get_transliterator


def test_basic_vowels():
    assert transliterate("a") == "अ"
    assert transliterate("aa") == "आ"
    assert transliterate("i") == "इ"
    assert transliterate("ii") == "ई"
    assert transliterate("u") == "उ"
    assert transliterate("e") == "ए"
    assert transliterate("o") == "ओ"


def test_consonants():
    assert transliterate("kha") == "ख"
    assert transliterate("gha") == "घ"
    assert transliterate("cha") == "च"


def test_compounds():
    assert transliterate("ksh") == "क्ष"
    assert transliterate("tr") == "त्र"
    assert transliterate("jn") == "ज्ञ"


def test_words():
    assert transliterate("namaste") == "नमस्ते"
    assert transliterate("kathmandu") == "काठमाडौं"
    assert transliterate("nepal") == "नेपाल"
    assert transliterate("namaskar") == "नमस्कार"
    assert transliterate("dhanyabad") == "धन्यवाद"


def test_matras():
    # kasto -> कस्तो (o matra on त)
    assert transliterate("kasto") == "कस्तो"
    # hello -> हेल्लो
    assert transliterate("hello") == "हेल्लो"


def test_numbers():
    assert transliterate("1 2 3") == "१ २ ३"


def test_punctuation():
    assert transliterate(".") == "।"


def test_suggestions():
    t = get_transliterator()
    _, suggs = t.transliterate_with_suggestions("nam")
    assert "namaste" in suggs


def test_retroflex_slash_forms():
    assert transliterate("t/") == "ट"
    assert transliterate("th/") == "ठ"
    assert transliterate("d/") == "ड"
    assert transliterate("dh/") == "ढ"
    assert transliterate("n/") == "ण"


def test_variant_consonants():
    assert transliterate("q") == "क"
    assert transliterate("c") == "क"
    assert transliterate("z") == "ज"
    assert transliterate("w") == "व"


def test_rri_vowel_priority():
    # multi-char vowel match must beat single consonant
    assert transliterate("rri") == "ऋ"
    assert transliterate("rree") == "ॠ"
    assert transliterate("krri") == "कृ"
    assert transliterate("kri") == "क्रि"


def test_short_i_matra():
    assert transliterate("ki") == "कि"
    assert transliterate("kii") == "की"


def test_midword_anuswar():
    assert transliterate("aM") == "अं"
    assert transliterate("sangaM") == "सँगं"


def test_avagraha_and_halant():
    assert transliterate("~a") == "ऽ"
    assert transliterate("\\") == "्‌"
    assert transliterate("nepal") == "नेपाल"
    assert transliterate("nepali") == "नेपाली"


def test_version_tag():
    import re
    from core import __version__
    assert re.match(r"^\d+\.\d+\.\d+$", __version__), __version__


def test_user_words():
    # words from real usage: nam->नाम (not नम), gosai->गोसाई
    assert transliterate("mero nam pradip gosai ho") == "मेरो नाम प्रदिप गोसाई हो"
    assert transliterate("gosain") == "गोसाईं"


def test_dictionary_growth():
    assert transliterate("sarkar") == "सरकार"
    assert transliterate("bidyalaya") == "बिद्यालय"
    assert transliterate("kasari") == "कसरी"
    assert transliterate("kahaa") == "कहाँ"
    assert transliterate("bhitra") == "भित्र"
    assert transliterate("dherai") == "धेरै"
    assert transliterate("aaja") == "आज"
    assert transliterate("garne") == "गर्ने"
    assert transliterate("bhayo") == "भयो"


def test_sentence_probes():
    assert transliterate("aayo") == "आयो"
    assert transliterate("bhaeko") == "भएको"
    assert transliterate("arko") == "अर्को"
    assert transliterate("garchhu") == "गर्छु"
    assert transliterate("shra") == "श्र"


def test_suggestions_ranked():
    t = get_transliterator()
    _, suggs = t.transliterate_with_suggestions("sa")
    assert suggs == sorted(suggs, key=lambda w: (len(w), w)) and len(suggs) <= 5


def test_auto_dictionary_quality():
    from core.words_auto import AUTO_CORRECTIONS as auto
    from core.dictionary import WORD_CORRECTIONS as hand
    # sizeable, all-Devanagari values, no overlap contradictions silently
    assert len(auto) > 5000
    for k, v in auto.items():
        assert k == k.lower() and k.isalpha() and k.isascii(), k
        assert len(v) >= 2, (k, v)
    # phonetic-owned keys must resolve to phonetic forms, not variants
    assert transliterate("anu") == "अनु"
    assert transliterate("mishra") == "मिश्र"
    assert transliterate("chhanda") == "छन्द"
    # known imported corrections resolve
    assert transliterate("kaki") == "काकी"
    assert transliterate("bhairahechha") == "भइरहेछ"
    # hand entries always win over auto
    assert transliterate("bolneharulai") == "बोल्नेहरूलाई"
    for k in hand:
        assert transliterate(k) == hand[k], k


def test_google_backend_optional():
    try:
        from core.google_backend import google_transliterate, google_sentence
        res = google_transliterate("namaste", num=2)
        assert res.get("namaste", [None])[0] == "नमस्ते"
        assert transliterate("namaste") == "नमस्ते"  # we agree here
        assert google_sentence("namaste kasto chha") == "नमस्ते कस्तो छ"
    except (OSError, RuntimeError) as e:
        print(f"  (skip test_google_backend_optional: offline/API down: {e})")


def test_candidates_ranking():
    import tempfile
    from core.nepali_transl import NepaliTransliterator
    old = os.environ.get("NEPALI_TRANSL_HOME")
    os.environ["NEPALI_TRANSL_HOME"] = tempfile.mkdtemp()
    try:
        t = NepaliTransliterator()
        # hand first, phonetic always last
        c = t.candidates("nam")
        assert c[0] == ("नाम", "hand"), c
        assert c[-1][1] == "phonetic", c
        assert t.candidates("") == []
        # user-learned outranks everything, then transliterate() agrees
        assert t.learn("nam", "नमX")
        c2 = t.candidates("nam")
        assert c2[0] == ("नमX", "user"), c2
        assert t.transliterate("nam") == "नमX"
        # bad learns rejected
        assert t.learn("", "x") is False
        assert t.learn("ok", "") is False
    finally:
        if old is None:
            os.environ.pop("NEPALI_TRANSL_HOME", None)
        else:
            os.environ["NEPALI_TRANSL_HOME"] = old


def test_top_matches_transliterate():
    from core.nepali_transl import get_transliterator
    t = get_transliterator()
    sample = ["namaste", "sangaM", "sangam", "aM", "kaki", "kathmandu",
              "nepal", "rri", "hello world", "timi kasto chha"]
    for w in sample:
        assert t.top(w) == t.transliterate(w), w


def test_merge_suggestions_pure():
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "web"))
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "webapp", os.path.join(os.path.dirname(__file__), "..", "web", "app.py"))
    webapp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(webapp)
    assert webapp.merge_suggestions(["a", "b"], ["b", "c", "d"]) == ["a", "b", "c", "d"]
    assert webapp.merge_suggestions(["a"], [], limit=8) == ["a"]
    assert len(webapp.merge_suggestions([], ["x"] * 20)) <= 8


def test_cli_google_optional():
    import io
    from contextlib import redirect_stdout
    try:
        from core.cli import main
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = main(["--google", "namaste"])
        assert rc == 0, rc
        assert buf.getvalue().strip() == "नमस्ते"
    except (OSError, RuntimeError) as e:
        print(f"  (skip test_cli_google_optional: offline/API down: {e})")


def test_preeti_bridge():
    import importlib.util
    if importlib.util.find_spec("preeti_unicode") is None:
        print("  (skip test_preeti_bridge: optional backend not installed)")
        return
    from core.preeti_bridge import preeti_to_unicode, detect_preeti, is_available
    assert is_available()
    assert preeti_to_unicode("asdfghjk") == "बकमानजवप"
    assert preeti_to_unicode("g]kfn") == "नेपाल"
    assert detect_preeti("g]kfn sf] ")
    assert not detect_preeti("hello world this is english")


def run_all():
    tests = [
        test_basic_vowels, test_consonants, test_compounds,
        test_words, test_matras, test_numbers,
        test_punctuation, test_suggestions,
        test_retroflex_slash_forms, test_variant_consonants,
        test_rri_vowel_priority, test_short_i_matra,
        test_midword_anuswar, test_avagraha_and_halant,
        test_dictionary_growth, test_version_tag, test_user_words,
        test_sentence_probes,
        test_suggestions_ranked, test_auto_dictionary_quality,
        test_google_backend_optional, test_cli_google_optional,
        test_merge_suggestions_pure, test_candidates_ranking,
        test_top_matches_transliterate, test_preeti_bridge,
    ]
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
    ok = run_all()
    sys.exit(0 if ok else 1)
