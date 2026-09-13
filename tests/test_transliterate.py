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
    assert suggs and all(s.startswith("nam") for s in suggs)
    _, suggs2 = t.transliterate_with_suggestions("kathm")
    assert "kathmandu" in suggs2


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
        top = res.get("namaste", [None])[0]
        # Don't pin Google's exact top-1 (it can change); assert usuable output.
        assert _devanagari(top), top
        assert transliterate("namaste") == "नमस्ते"  # ours is stable
        assert _devanagari(google_sentence("namaste kasto chha"))
    except (OSError, RuntimeError) as e:
        print(f"  (skip test_google_backend_optional: offline/API down: {e})")


def _devanagari(s):
    import unicodedata
    return bool(s) and all(
        unicodedata.name(c, "").startswith("DEVANAGARI") or c in " ।॥"
        for c in s)


def test_candidates_ranking():
    import tempfile
    from core.nepali_transl import NepaliTransliterator
    old = os.environ.get("NEPALI_TRANSL_HOME")
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["NEPALI_TRANSL_HOME"] = tmp
        try:
            t = NepaliTransliterator()
            # hand first, phonetic always present
            c = t.candidates("nam")
            assert c[0] == ("नाम", "hand"), c
            assert any(s == "phonetic" for _, s in c), c
            assert t.candidates("") == []
            # user-learned outranks everything, then transliterate() agrees
            assert t.learn("nam", "नमX")
            c2 = t.candidates("nam")
            assert c2[0] == ("नमX", "user"), c2
            assert t.transliterate("nam") == "नमX"
            # persists across instances (same lexicon dir)
            t2 = NepaliTransliterator()
            assert t2.top("nam") == "नमX"
            # bad learns rejected
            assert t.learn("", "x") is False
            assert t.learn("ok", "") is False
        finally:
            if old is None:
                os.environ.pop("NEPALI_TRANSL_HOME", None)
            else:
                os.environ["NEPALI_TRANSL_HOME"] = old


def test_file_and_batch_apis():
    import tempfile
    from core.nepali_transl import get_transliterator
    t = get_transliterator()
    assert t.correct_word("namaste") == "नमस्ते"
    assert t.correct_word("zzzznonsense") is None
    assert t.batch_transliterate(["namaste", "kha"]) == ["नमस्ते", "ख"]
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False,
                                     encoding="utf-8") as f:
        f.write("namaste")
        path = f.name
    try:
        assert t.transliterate_file(path) == "नमस्ते"
    finally:
        os.unlink(path)


def test_fuzzy_variants():
    # loose spellings surface canonical forms as alternates WITHOUT
    # hijacking top-1 (short words like ki/anu must stay phonetic).
    t = get_transliterator()
    c = t.candidates("kaathmaandu")
    assert ("काठमाडौं", "fuzzy:hand") in c, c
    assert c[0][0] == t.transliterate("kaathmaandu")  # top-1 agreement
    assert any(s == "phonetic" for _, s in c)  # phonetic always present
    c2 = t.candidates("kathamandu")
    assert any(f == "काठमाडौं" and s.startswith("deschwa")
               for f, s in c2), c2
    # exact + short words unaffected by fuzzy
    assert t.transliterate("ki") == "कि"
    assert t.transliterate("anu") == "अनु"
    assert t.transliterate("nepaal") == "नेपाल"


def test_roman_corpus_words():
    # frequent real typed forms from Nepali-Flow-Roman
    assert transliterate("xa") == "छ"
    assert transliterate("xaina") == "छैन"
    assert transliterate("haru") == "हरू"
    assert transliterate("malai") == "मलाई"
    assert transliterate("hunxa") == "हुन्छ"
    assert transliterate("hamro") == "हाम्रो"
    assert transliterate("vayo") == "भयो"
    assert transliterate("lagyo") == "लाग्यो"
    t = get_transliterator()
    assert "xaina" in t._dictionary and "vayo" in t._dictionary


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
        assert _devanagari(buf.getvalue().strip())
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
        test_top_matches_transliterate, test_fuzzy_variants,
        test_roman_corpus_words, test_file_and_batch_apis,
        test_preeti_bridge,
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
