"""
nepali-transl - Modern Nepali Roman Transliteration Engine
Based on the ne-rom-translit.mim input method (m17n database)
"""

import json
import os
import re
from typing import Optional, Tuple, List, Dict

try:
    from .dictionary import WORD_CORRECTIONS, SUGGESTION_WORDS
except ImportError:
    from dictionary import WORD_CORRECTIONS, SUGGESTION_WORDS

try:
    from .words_auto import AUTO_CORRECTIONS
except ImportError:
    try:
        from words_auto import AUTO_CORRECTIONS
    except ImportError:
        AUTO_CORRECTIONS = {}  # generated file absent: regenerate via tools/

try:
    from .words_suggest import ROMAN_SUGGESTIONS
except ImportError:
    try:
        from words_suggest import ROMAN_SUGGESTIONS
    except ImportError:
        ROMAN_SUGGESTIONS = []  # regenerate via tools/import_roman.py


# Core mapping data extracted from ne-rom-translit.mim
CONSONANT_MAP = {
    # Multi-char consonant clusters (longest first)
    'ksh': 'क्ष', 'ng': 'ङ', 'chh': 'छ', 'yn': 'ञ',
    'th/': 'ठ', 'dh/': 'ढ', 'n/': 'ण', 't/': 'ट', 'd/': 'ड',
    'shh': 'ष', 'gyn': 'ज्ञ', 'gy': 'ग्य',
    # Single consonants
    'kh': 'ख', 'gh': 'घ', 'ch': 'च', 'jh': 'झ',
    'T': 'ट', 'Th': 'ठ', 'D': 'ड', 'Dh': 'ढ',
    'k': 'क', 'g': 'ग',
    't': 'त', 'th': 'थ', 'd': 'द', 'dh': 'ध', 'n': 'न',
    'p': 'प', 'f': 'फ', 'ph': 'फ', 'b': 'ब', 'bh': 'भ', 'm': 'म',
    'y': 'य', 'r': 'र', 'R': 'र', 'l': 'ल', 'v': 'व', 'w': 'व',
    'sh': 'श', 'Sh': 'ष', 's': 'स', 'h': 'ह',
    'ks': 'क्स', 'x': 'क्स',
    # Also accept c, q, z as variant of क
    'c': 'क', 'q': 'क', 'j': 'ज', 'z': 'ज',
}

# Independent vowels (standalone, at start of word or after pause)
# NOTE: lowercase om/aum are handled as word-initial only (see _transliterate_word):
# "om" alone -> ॐ, but "sombar" keeps o+m separate (सोमबार), matching Google.
INDEPENDENT_VOWELS = {
    'AUM': 'ॐ', 'OM': 'ॐ', 'a': 'अ', 'aa': 'आ', 'A': 'आ',
    'i': 'इ', 'I': 'ई', 'ee': 'ई', 'ii': 'ई',
    'u': 'उ', 'U': 'ऊ', 'uu': 'ऊ', 'oo': 'ऊ',
    'rri': 'ऋ', 'rree': 'ॠ', 'rrii': 'ॄ',
    'e': 'ए', 'ai': 'ऐ', 'o': 'ओ', 'au': 'औ',
}

# Dependent vowels (matras - follow consonants)
# NOTE: 'a' is inherent vowel -> empty string (from mim: ("a" ""))
DEPENDENT_VOWELS = {
    'a': '', 'aa': 'ा', 'A': 'ा',
    'i': 'ि', 'I': 'ी', 'ee': 'ी', 'ii': 'ी',
    'u': 'ु', 'U': 'ू', 'uu': 'ू', 'oo': 'ू',
    'rri': 'ृ', 'rrii': 'ॄ',
    'e': 'े', 'ai': 'ै', 'o': 'ो', 'au': 'ौ',
}

# Anuswar (anusvara)
ANUSWAR = {'*': 'ँ', 'M': 'ं', 'N': 'ं', 'H': 'ः'}

# Purna viram (full stop)
PUNNA_VIRAM = {'.': '।', '..': '॥', '~a': 'ऽ', '~': '।'}

# Explicit halant forms from ne-rom-translit.mim
HALANT = '्'
HALANT_ZWNJ = '्‌'       # "\\" in mim: halant + ZWNJ (break conjunct, no join)
ZWNJ_HALANT_ZWJ = '‌्‍'  # "|" in mim: ZWNJ + halant + ZWJ (explicit half form)

# Numbers
NUMBERS = {'0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
           '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'}

# Compound consonant handling: (consonant, next_consonant) → conjunct
COMPOUND_RULES = {
    ('क', 'ष'): 'क्ष', ('क', 'स'): 'क्स',
    ('ग', 'य'): 'ग्य', ('ज', 'ञ'): 'ज्ञ',
    ('त', 'र'): 'त्र', ('त', 'न'): 'त्न',
    ('ज', 'न'): 'ज्ञ', ('ज', 'य'): 'ज्य',
    ('श', 'र'): 'श्र', ('श', 'व'): 'श्व',
    ('स', 'त'): 'स्त', ('स', 'क'): 'स्क',
    ('न', 'द'): 'न्द', ('न', 'ध'): 'न्ध',
    ('र', 'र'): 'र्र', ('र', 'य'): 'र्य',
}

# Matra characters (used to detect if a char is a dependent vowel)
MATRA_SET = set(DEPENDENT_VOWELS.values())

# Devanagari digits (for the decimal-point rule: digit.digit keeps '.').
_DEVA_DIGITS = frozenset(NUMBERS.values())

# Edge punctuation stripped for dictionary lookup, then re-attached
# transliterated (so "kathmandu," still hits the dictionary and the comma
# survives; interior markers like t/ ~a \\ are NEVER stripped).
_STRIP_LEAD = "\"'([{<\u00ab\u2018\u201c\u2014\u2013"
_STRIP_TRAIL = ",;:!?.)]}'\"\u00bb\u2019\u201d\u2026\u2014\u2013"

# Productive case suffixes: stem (in dictionaries) + suffix compose
# (timi+lai -> तिमीलाई). Two-char suffixes need stems of len>=4 to avoid
# hijacking short words (kama stays काम, not काममा).
_SUFFIX_TABLE = {
    "harulai": "हरूलाई", "haruma": "हरूमा", "haruko": "हरूको",
    "harubata": "हरूबाट", "harule": "हरूले",
    "laai": "लाई", "lai": "लाई",
    "baata": "बाट", "bata": "बाट",
    "dekhi": "देखि", "samma": "सम्म",
    "sangai": "सँगै", "sanga": "सँग",
    "dwara": "द्वारा", "prati": "प्रति",
    "haru": "हरू",
    "ko": "को", "ka": "का", "ki": "की",
    "ma": "मा", "maa": "मा", "le": "ले",
}

# Latin-domain endings for URL passthrough.
_TLDS = (".com", ".np", ".org", ".net", ".edu", ".gov", ".info", ".io")

_VOWEL_LETTERS = frozenset("aeiou")


def _collapse_vowels(key: str) -> str:
    """Collapse runs of the same vowel: kaathmaandu -> kathmandu.

    Doubled consonants are kept (chhatra stays chhatra). Used to build
    and query the fuzzy index so spelling variants share one entry.
    """
    out = []
    prev = ""
    for ch in key:
        if ch == prev and ch in _VOWEL_LETTERS:
            continue
        out.append(ch)
        prev = ch
    return "".join(out)


def _deschwa_key(key: str) -> str:
    """Drop interior short-a: kathamandu -> kthmndu.

    Only meaningful for longer keys (callers guard len>=6); short words
    over-collapse (ram -> rm), so they never enter the deschwa index.
    """
    if len(key) < 2:
        return key
    return key[0] + "".join(ch for ch in key[1:] if ch != "a")


class NepaliTransliterator:
    """Converts romanized Nepali text to Devanagari Unicode using state machine."""

    def __init__(self):
        self._load_mappings()
        self._dictionary = self._load_dictionary()

    def _load_mappings(self):
        # Sort consonant keys by length descending for priority matching
        self._consonant_keys = sorted(
            list(CONSONANT_MAP.keys()), key=len, reverse=True
        )
        self._vowel_keys = sorted(
            list(INDEPENDENT_VOWELS.keys()), key=len, reverse=True
        )
        self._matra_keys = sorted(
            list(DEPENDENT_VOWELS.keys()), key=len, reverse=True
        )

    def _load_dictionary(self) -> set:
        """Load suggestion pool + fuzzy lookup indexes.

        Fuzzy indexes (idea: pratt778/nepali_transliteration, reimplemented):
        vowel-collapsed keys (kaathmaandu/kathmandu -> kathmandu) and,
        for longer keys only, deschwa keys (kathamandu -> kthmndu) so
        loose spellings still find dictionary forms.
        """
        pool = (set(SUGGESTION_WORDS) | set(AUTO_CORRECTIONS.keys())
                | set(ROMAN_SUGGESTIONS))
        self._fuzzy_index: Dict[str, List[Tuple[str, str]]] = {}
        self._deschwa_index: Dict[str, List[Tuple[str, str]]] = {}
        for source, table in (("hand", WORD_CORRECTIONS),
                              ("auto", AUTO_CORRECTIONS)):
            for key, form in table.items():
                # Every entry is reachable under its collapsed key, so
                # spelling variants (kaathmaandu) find canonical entries
                # (kathmandu). Exact hits still rank first (checked before).
                nk = _collapse_vowels(key)
                self._fuzzy_index.setdefault(nk, []).append((form, source))
                if len(key) >= 6:
                    dk = _deschwa_key(key)
                    if dk != nk:
                        self._deschwa_index.setdefault(dk, []).append(
                            (form, source))
        return pool

    def correct_word(self, word: str) -> Optional[str]:
        """Return dictionary correction for a word, if known."""
        key = word.lower()
        user = self._user_lexicon()
        return user.get(key, WORD_CORRECTIONS.get(
            key, AUTO_CORRECTIONS.get(key)))

    # ---- user lexicon (local learning, never shipped) ----

    @staticmethod
    def _lexicon_path() -> str:
        base = os.environ.get("NEPALI_TRANSL_HOME")
        if not base:
            base = os.path.join(os.path.expanduser("~"), ".config",
                                "nepali-transliterate")
        return os.path.join(base, "user.json")

    def _user_lexicon(self) -> Dict[str, str]:
        """Per-user learned mappings {roman: devanagari} ({} if none)."""
        if hasattr(self, "_user_cache"):
            return self._user_cache
        self._user_cache = {}
        try:
            with open(self._lexicon_path(), encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                self._user_cache = {str(k).lower(): str(v)
                                    for k, v in data.items()}
        except (OSError, ValueError):
            pass
        return self._user_cache

    def learn(self, roman: str, devanagari: str) -> bool:
        """Remember a user's choice locally. Returns True if stored."""
        roman = (roman or "").strip().lower()
        devanagari = (devanagari or "").strip()
        if not roman or not devanagari or len(roman) > 40:
            return False
        lex = self._user_lexicon()
        if lex.get(roman) == devanagari:
            return True  # already known
        lex[roman] = devanagari
        try:
            os.makedirs(os.path.dirname(self._lexicon_path()), exist_ok=True)
            with open(self._lexicon_path(), "w", encoding="utf-8") as f:
                json.dump(lex, f, ensure_ascii=False, indent=1,
                          sort_keys=True)
        except OSError:
            return False
        return True

    @staticmethod
    def _split_affixes(word: str) -> Tuple[str, str, str]:
        """Split edge punctuation: ("kathmandu,") -> ("", "kathmandu", ",").

        Only edge characters are stripped; interior markers (t/, ~a, dots
        in 15.50) are untouched, so this always terminates.
        """
        i = 0
        while i < len(word) and word[i] in _STRIP_LEAD:
            i += 1
        j = len(word)
        while j > i and word[j - 1] in _STRIP_TRAIL:
            j -= 1
        return word[:i], word[i:j], word[j:]

    def _latin_keep(self, core: str) -> Optional[str]:
        """Words that must stay Latin: emails, URLs, ALL-CAPS acronyms.

        Returns the word unchanged, or None to continue transliterating.
        Dict-known capitals (KATHMANDU) still resolve via dictionaries;
        OM/AUM still give ॐ via phonetics.
        """
        if "@" in core:
            return core  # email address: never transliterate
        low = core.lower()
        if "://" in core or low.startswith("www."):
            return core
        if low.endswith(_TLDS):
            return core
        if (len(core) > 1 and core.isupper()
                and core not in ("OM", "AUM")
                and low not in WORD_CORRECTIONS
                and low not in AUTO_CORRECTIONS
                and low not in self._user_lexicon()):
            return core  # CDO, NGO... (Devanagari has no capitals)
        return None

    def _split_compound(self, core: str) -> Optional[Tuple[str, str]]:
        """Productive stem+suffix composition (timi+lai -> तिमीलाई).

        Returns (form, "compound") or None. Whole-word dictionary hits
        always take precedence (checked before calling this).
        """
        key = core.lower()
        for suffix in sorted(_SUFFIX_TABLE, key=len, reverse=True):
            if len(key) <= len(suffix) or not key.endswith(suffix):
                continue
            stem = key[:-len(suffix)]
            if len(suffix) <= 2 and len(stem) < 4:
                continue  # kama stays काम, jasko handled by hand dict
            if len(suffix) > 2 and len(stem) < 3:
                continue
            user = self._user_lexicon()
            if stem in user:
                return user[stem] + _SUFFIX_TABLE[suffix], "compound:user"
            if stem in WORD_CORRECTIONS:
                return (WORD_CORRECTIONS[stem] + _SUFFIX_TABLE[suffix],
                        "compound:hand")
            if stem in AUTO_CORRECTIONS:
                return (AUTO_CORRECTIONS[stem] + _SUFFIX_TABLE[suffix],
                        "compound:auto")
        return None

    def _stem_mark(self, word: str) -> Optional[Tuple[str, str]]:
        """Trailing M/N/H/* applied to a resolvable stem (single level).

        Returns (form, origin-source) or None. Origin mirrors the stem's
        own source so ranking stays truthful.
        """
        if len(word) <= 1 or word[-1] not in ANUSWAR:
            return None
        stem_key = word[:-1].lower()
        if not stem_key or stem_key[-1:] in ANUSWAR:
            return None  # no chained stems (sangaMM etc.)
        user = self._user_lexicon()
        if stem_key in user:
            return user[stem_key] + ANUSWAR[word[-1]], "user"
        if stem_key in WORD_CORRECTIONS:
            return WORD_CORRECTIONS[stem_key] + ANUSWAR[word[-1]], "hand"
        if stem_key in AUTO_CORRECTIONS:
            return AUTO_CORRECTIONS[stem_key] + ANUSWAR[word[-1]], "auto"
        return None

    # ---- candidate generation + ranking ----

    def _ranked(self, word: str) -> List[Tuple[str, str]]:
        """Ordered (form, source) list for one word.

        First entry is ALWAYS the top-1 transliterate() output, so
        ranking can never disagree with typing (both read _ranked_core).
        After it come fuzzy/deschwa alternates; phonetic is always
        present. Edge punctuation is transliterated and attached to
        every form. Contract: SINGLE word (phrases: use top()).
        """
        pre, core, suf = self._split_affixes(word or "")
        key = core.lower()
        if not key or any(ch.isspace() for ch in key):
            return []
        out: List[Tuple[str, str]] = []
        seen = set()

        def add(form, source):
            if form and form not in seen:
                seen.add(form)
                out.append((form, source))

        for form, source in self._ranked_core(core):
            add(form, source)
        for form, source in self._fuzzy_index.get(
                _collapse_vowels(key), [])[:2]:
            add(form, "fuzzy:" + source)
        if len(key) >= 6:
            for form, source in self._deschwa_index.get(
                    _deschwa_key(key), [])[:2]:
                add(form, "deschwa:" + source)
        add(self._phonetic(core), "phonetic")
        if not pre and not suf:
            return out
        pre_ph = self._phonetic(pre)
        suf_ph = self._phonetic(suf)
        return [(pre_ph + form + suf_ph, source) for form, source in out]

    def candidates(self, word: str,
                   dictionary: bool = True) -> List[Tuple[str, str]]:
        """Ranked Devanagari candidates for one romanized word.

        Contract: SINGLE word only (returns [] for phrases/empty; use
        top()/transliterate() for those). First entry is ALWAYS the
        top-1 transliterate() output; after it come fuzzy/deschwa
        alternates, then the phonetic reading if not already shown.
        The phonetic form is ALWAYS present (last resort).
        dictionary=False: pure rules, exactly [(phonetic, 'phonetic')].
        """
        if not dictionary:
            ph = self._transliterate_word(word or "", use_dict=False)
            return [(ph, "phonetic")] if ph else []
        return self._ranked(word)

    def top(self, text: str, dictionary: bool = True) -> str:
        """Best single form. Delegates to transliterate() so the two can
        never disagree (candidates() is single-word; transliterate()
        handles phrases word by word)."""
        return self.transliterate(text, dictionary=dictionary)

    MODES = ("roman", "traditional", "traditional-kmn", "romanized")

    def transliterate(self, text: str, mode: str = "roman",
                      dictionary: bool = True) -> str:
        """Main entry point.

        mode="roman": transliterate romanized phonetics to Devanagari.
        mode="traditional": direct MPP Traditional key mapping.
        mode="traditional-kmn": revised Traditional mapping (Keyman v1.3.1).
        mode="romanized": direct MPP Romanized key mapping.
        Direct modes map each key as-is: no phonetics, no dictionary.

        dictionary=False: pure m17n-style rules only — no word corrections,
        no learning, no composition. Deterministic: kaama always gives
        काम, kama always gives कम. (No rule can tell kama/kamal apart
        without a dictionary; that is why the layer exists at all.)
        """
        if not text:
            return ""
        if mode in ("traditional", "traditional-kmn", "romanized"):
            try:
                from .traditional import traditional_type, traditional_kmn_type
                from .romanized_layout import romanized_type
            except ImportError:
                from traditional import traditional_type, traditional_kmn_type
                from romanized_layout import romanized_type
            return {"traditional": traditional_type,
                    "traditional-kmn": traditional_kmn_type,
                    "romanized": romanized_type}[mode](text)
        if mode != "roman":
            raise ValueError(f"unknown mode: {mode!r} {self.MODES}")

        # Split on whitespace runs, keeping the separators, so newlines,
        # tabs and multi-spaces survive verbatim AND every word gets its
        # own dictionary lookup (glued "X\\npani" tokens used to miss).
        parts = re.split(r'(\s+)', text)
        return ''.join(
            p if not p or p[0].isspace()
            else self._transliterate_word(p, use_dict=dictionary)
            for p in parts
        )

    def _ranked_core(self, core: str) -> List[Tuple[str, str]]:
        """Ordered (form, source) for a punctuation-free core word.

        user > stem+mark > hand > auto > compound > latin >
        phonetic (always present). Single source of truth: both
        transliterate() top-1 and candidates() read from here.
        """
        key = core.lower()
        out: List[Tuple[str, str]] = []
        seen = set()

        def add(form, source):
            if form and form not in seen:
                seen.add(form)
                out.append((form, source))

        add(self._user_lexicon().get(key), "user")
        stemmed = self._stem_mark(core)
        if stemmed:
            add(*stemmed)
        add(WORD_CORRECTIONS.get(key), "hand")
        add(AUTO_CORRECTIONS.get(key), "auto")
        compound = self._split_compound(core)
        if compound:
            add(*compound)
        add(self._latin_keep(core), "latin")
        add(self._transliterate_word(core, use_dict=False), "phonetic")
        return out

    def _transliterate_word(self, word: str, use_dict: bool = True) -> str:
        """Transliterate a single word using state machine."""
        if not word:
            return ""
        # Strip edge punctuation so "kathmandu," hits the dictionary;
        # affixes are transliterated separately and re-attached.
        # Fuzzy variants NEVER decide top-1 (they misfire on short
        # words); they only appear as click-to-learn alternates.
        if use_dict:
            pre, core, suf = self._split_affixes(word)
            if not core:
                return self._transliterate_word(pre + suf, use_dict=False)
            ranked = self._ranked_core(core)
            top = ranked[0][0] if ranked else self._phonetic(core)
            return (self._phonetic(pre) + top
                    + self._phonetic(suf))

        return self._phonetic(word)

    def _phonetic(self, word: str) -> str:
        """Raw state machine: no dictionaries, no affix logic."""
        result = []
        i = 0
        pending_consonant: Optional[str] = None

        while i < len(word):
            # Word-initial om/aum -> ॐ (elsewhere o+m stay separate: sombar).
            if i == 0:
                if word[0:3] == 'aum':
                    result.append('ॐ')
                    i += 3
                    continue
                if word[0:2] == 'om':
                    result.append('ॐ')
                    i += 2
                    continue
            # Check for numbers
            if word[i] in NUMBERS:
                if pending_consonant:
                    result.append(pending_consonant)
                    pending_consonant = None
                result.append(NUMBERS[word[i]])
                i += 1
                continue

            # Check for purna viram (but keep decimal points: 15.50)
            if word[i] == '.':
                if pending_consonant:
                    result.append(pending_consonant)
                    pending_consonant = None
                if i + 1 < len(word) and word[i + 1] == '.':
                    result.append(PUNNA_VIRAM['..'])
                    i += 2
                elif (result and result[-1] in _DEVA_DIGITS
                        and i + 1 < len(word)
                        and (word[i + 1] in NUMBERS
                             or word[i + 1] in _DEVA_DIGITS)):
                    result.append('.')
                    i += 1
                else:
                    result.append(PUNNA_VIRAM['.'])
                    i += 1
                continue

            # Check for anuswar characters
            # M/N are context-sensitive: consonant at word start, anuswar mid-word
            # e.g. "Nepal" N->न, but "aM" M->ं and "sangaM" M->ं
            if word[i] in ANUSWAR:
                at_word_start = not pending_consonant and not result
                if word[i] in ('M', 'N') and at_word_start:
                    # Fall through to consonant handling (treat as m/n)
                    pass
                else:
                    if pending_consonant:
                        result.append(pending_consonant)
                        pending_consonant = None
                    result.append(ANUSWAR[word[i]])
                    i += 1
                    continue

            # Try consonant AND independent-vowel matches; prefer the LONGEST
            # (so 'rri'->ऋ beats 'r'->र, but 'ra' still gives र).
            consonant_match = self._match_consonant(word, i)
            vowel_match = self._match_independent_vowel(word, i)
            if (consonant_match and vowel_match
                    and vowel_match[2] > consonant_match[2]):
                consonant_match = None
            if consonant_match:
                matched_str, nepali_char, consumed = consonant_match

                # If we have a pending consonant, combine them
                if pending_consonant:
                    compound = self._make_compound(pending_consonant, nepali_char)
                    if compound:
                        # Keep compound as pending so matras can attach
                        # e.g. s+t -> स्त pending, then e -> स्ते
                        pending_consonant = compound
                    else:
                        result.append(pending_consonant)
                        pending_consonant = nepali_char
                else:
                    pending_consonant = nepali_char

                i += consumed
                continue

            # Independent vowel (standalone, or matra when following a consonant)
            if vowel_match:
                matched_str, nepali_char, consumed = vowel_match

                if pending_consonant:
                    # Apply matra (note: 'a' -> '' is valid, so check is not None)
                    matra = DEPENDENT_VOWELS.get(matched_str)
                    if matra is not None:
                        result.append(pending_consonant + matra)
                    else:
                        result.append(pending_consonant + nepali_char)
                    pending_consonant = None
                else:
                    result.append(nepali_char)

                i += consumed
                continue

            # NOTE: there is intentionally no separate dependent-vowel
            # (matra) branch here: every matra key is also an independent
            # key, so the branch above always matches first and applies
            # the matra via DEPENDENT_VOWELS. (_match_dependent_vowel is
            # kept for external/test use.)

            # Explicit halant forms (from mim: "\\"->halant+ZWNJ, "|"->ZWNJ+halant+ZWJ)
            if word[i] == '\\' or word[i] == '|':
                if pending_consonant:
                    result.append(pending_consonant)
                    pending_consonant = None
                result.append(HALANT_ZWNJ if word[i] == '\\' else ZWNJ_HALANT_ZWJ)
                i += 1
                continue

            # Tilde: "~a" -> avagraha ऽ, lone "~" -> ।
            if word[i] == '~':
                if pending_consonant:
                    result.append(pending_consonant)
                    pending_consonant = None
                if word[i + 1:i + 2] == 'a':
                    result.append(PUNNA_VIRAM['~a'])
                    i += 2
                else:
                    result.append(PUNNA_VIRAM['~'])
                    i += 1
                continue

            # Unknown character - flush pending consonant
            if pending_consonant:
                result.append(pending_consonant)
                pending_consonant = None
            result.append(word[i])
            i += 1

        # Flush any remaining pending consonant
        if pending_consonant:
            result.append(pending_consonant)

        return ''.join(result)

    def _match_consonant(self, word: str, pos: int) -> Optional[Tuple[str, str, int]]:
        """Try to match a consonant at position pos. Returns (matched_str, nepali_char, consumed)."""
        for key in self._consonant_keys:
            if word[pos:pos + len(key)] == key:
                return (key, CONSONANT_MAP[key], len(key))
        # Fallback: uppercase M/N -> consonant m/n (at word start)
        # and other uppercase consonants -> lowercase equivalent
        # (except T,D,Sh,Th,Dh which are distinct retroflex)
        ch = word[pos] if pos < len(word) else ''
        if ch in ('M', 'N'):
            return (ch, 'म' if ch == 'M' else 'न', 1)
        if ch.isupper() and ch.lower() in CONSONANT_MAP:
            # Don't override distinct retroflex/caps already in map
            if ch not in CONSONANT_MAP:
                return (ch, CONSONANT_MAP[ch.lower()], 1)
        return None

    def _match_independent_vowel(self, word: str, pos: int) -> Optional[Tuple[str, str, int]]:
        """Try to match an independent vowel."""
        for key in self._vowel_keys:
            if word[pos:pos + len(key)] == key:
                return (key, INDEPENDENT_VOWELS[key], len(key))
        return None

    def _match_dependent_vowel(self, word: str, pos: int) -> Optional[Tuple[str, str, int]]:
        """Try to match a dependent vowel (matra)."""
        for key in self._matra_keys:
            if word[pos:pos + len(key)] == key:
                return (key, DEPENDENT_VOWELS[key], len(key))
        return None

    def _make_compound(self, c1: str, c2: str) -> Optional[str]:
        """Try to create a compound consonant from two consonants."""
        # Check direct compound rule
        if (c1, c2) in COMPOUND_RULES:
            return COMPOUND_RULES[(c1, c2)]

        # If c2 is already a halant+consonant, keep as is
        # Otherwise, add halant between them
        if c2 not in MATRA_SET and not c2.startswith(HALANT):
            return c1 + HALANT + c2
        return None

    def transliterate_with_suggestions(
            self, text: str,
            dictionary: bool = True) -> Tuple[str, List[str]]:
        """Transliterate and get word suggestions for the last word."""
        words = text.split()
        last_word = words[-1] if words else ""
        suggestions = (self._get_suggestions(last_word.lower())
                       if dictionary else [])
        result = self.transliterate(text, dictionary=dictionary)
        return result, suggestions

    def _get_suggestions(self, prefix: str) -> List[str]:
        """Get word suggestions based on prefix, shortest-first."""
        if not prefix:
            return []
        matches = [w for w in self._dictionary if w.startswith(prefix)]
        matches.sort(key=lambda w: (len(w), w))
        return matches[:5]

    def transliterate_file(self, filepath: str) -> str:
        """Read a file and transliterate its contents."""
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.transliterate(content)

    def batch_transliterate(self, texts: List[str]) -> List[str]:
        """Transliterate multiple texts at once."""
        return [self.transliterate(t) for t in texts]


# Global instance
_transliterator = None

def get_transliterator() -> NepaliTransliterator:
    """Get the global transliterator instance."""
    global _transliterator
    if _transliterator is None:
        _transliterator = NepaliTransliterator()
    return _transliterator


def transliterate(text: str, mode: str = "roman",
                  dictionary: bool = True) -> str:
    """Convenience function: romanized (or traditional) text to Devanagari."""
    return get_transliterator().transliterate(text, mode=mode,
                                              dictionary=dictionary)


def transliterate_with_suggestions(text: str,
                                   dictionary: bool = True) -> Tuple[str, List[str]]:
    """Transliterate and return suggestions."""
    return get_transliterator().transliterate_with_suggestions(
        text, dictionary=dictionary)


if __name__ == '__main__':
    t = NepaliTransliterator()

    test_cases = [
        "namaste",
        "kathmandu",
        "kasto chha",
        "hello namaste",
        "kha gha cha",
        "ksh",
        "tr",
        "jn",
        "namaskar dhanyabad",
        "1 2 3",
        "namaste kasto chha",
        "Ramro Nepal",
        "khaana khana",
        "ma sanga",
    ]

    print("=== Nepali Transliteration Tests ===\n")
    for test in test_cases:
        result = t.transliterate(test)
        print(f"  {test:35s} -> {result}")

    print("\n=== Suggestions ===\n")
    for prefix in ['nam', 'kas', 'dhany', 'ram']:
        suggs = t._get_suggestions(prefix)
        print(f"  '{prefix}' -> {suggs}")
