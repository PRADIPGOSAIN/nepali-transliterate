"""
nepali-transl - Modern Nepali Roman Transliteration Engine
Based on the ne-rom-translit.mim input method (m17n database)
"""

import re
import json
import os
from typing import Optional, Tuple, List, Dict
from pathlib import Path

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


class NepaliTransliterator:
    """Converts romanized Nepali text to Devanagari Unicode using state machine."""

    def __init__(self, dict_path: Optional[str] = None):
        self._load_mappings()
        self._dict_path = dict_path or str(Path(__file__).parent / "dictionary.db")
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
        """Load suggestion pool: hand wordlist + auto-imported keys."""
        return set(SUGGESTION_WORDS) | set(AUTO_CORRECTIONS.keys())

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

    def candidates(self, word: str) -> List[Tuple[str, str]]:
        """Ranked Devanagari candidates for one romanized word.

        Sources vote in priority order; first occurrence wins, order kept:
          user lexicon > hand dictionary > auto dictionary > phonetics.
        The phonetic form is ALWAYS present (last resort). Returns
        [(form, source)] with source in {user, hand, auto, phonetic}.
        """
        key = (word or "").strip().lower()
        if not key:
            return []
        out: List[Tuple[str, str]] = []
        seen = set()

        def add(form, source):
            if form and form not in seen:
                seen.add(form)
                out.append((form, source))

        # Mirror _transliterate_word priority exactly (user, stem, hand...).
        add(self._user_lexicon().get(key), "user")
        stemmed = self._stem_mark(word)
        if stemmed:
            add(*stemmed)
        add(WORD_CORRECTIONS.get(key), "hand")
        add(AUTO_CORRECTIONS.get(key), "auto")
        # NOTE: phonetic runs on the ORIGINAL word: case is meaningful
        # (trailing M = anusvara, m = consonant: aM->अं but am->अम).
        add(self._transliterate_word(word, use_dict=False), "phonetic")
        return out

    def top(self, text: str) -> str:
        """Best single form. Delegates to transliterate() so the two can
        never disagree (candidates() is single-word; transliterate()
        handles phrases word by word)."""
        return self.transliterate(text)

    MODES = ("roman", "traditional", "traditional-kmn", "romanized")

    def transliterate(self, text: str, mode: str = "roman") -> str:
        """Main entry point.

        mode="roman": transliterate romanized phonetics to Devanagari.
        mode="traditional": direct MPP Traditional key mapping.
        mode="traditional-kmn": revised Traditional mapping (Keyman v1.3.1).
        mode="romanized": direct MPP Romanized key mapping.
        Direct modes map each key as-is: no phonetics, no dictionary.
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

        # Split by whitespace, process each word
        words = text.split(' ')
        result_words = []

        for word in words:
            result_words.append(self._transliterate_word(word))

        return ' '.join(result_words)

    def _transliterate_word(self, word: str, use_dict: bool = True) -> str:
        """Transliterate a single word using state machine."""
        if not word:
            return ""
        # Dictionary autocorrect first: user-learned, hand, auto-imported.
        # (handles kathmandu->काठमाडौं etc.)
        if use_dict:
            user_hit = self._user_lexicon().get(word.lower())
            if user_hit:
                return user_hit
            # Trailing anuswar/visarga keystroke (capital M/N/H or *):
            # in mim these keystrokes ARE the anusvara, so "sangaM" must read
            # as stem+mark (सँगं), never as lowercase whole-word ("sangam").
            stemmed = self._stem_mark(word)
            if stemmed:
                return stemmed[0]
            key = word.lower()
            correction = WORD_CORRECTIONS.get(key, AUTO_CORRECTIONS.get(key))
            if correction:
                return correction

        result = []
        i = 0
        pending_halant = False
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

            # Check for purna viram
            if word[i] == '.':
                if pending_consonant:
                    result.append(pending_consonant)
                    pending_consonant = None
                if i + 1 < len(word) and word[i + 1] == '.':
                    result.append(PUNNA_VIRAM['..'])
                    i += 2
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

            # Try to match dependent vowel (matra)
            matra_match = self._match_dependent_vowel(word, i)
            if matra_match:
                matched_str, nepali_char, consumed = matra_match

                if pending_consonant:
                    result.append(pending_consonant + nepali_char)
                    pending_consonant = None
                else:
                    # Standalone matra - unlikely but handle gracefully
                    result.append(nepali_char)

                i += consumed
                continue

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

    def transliterate_with_suggestions(self, text: str) -> Tuple[str, List[str]]:
        """Transliterate and get word suggestions for the last word."""
        words = text.split()
        last_word = words[-1] if words else ""
        suggestions = self._get_suggestions(last_word.lower())
        result = self.transliterate(text)
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


def transliterate(text: str, mode: str = "roman") -> str:
    """Convenience function: romanized (or traditional) text to Devanagari."""
    return get_transliterator().transliterate(text, mode=mode)


def transliterate_with_suggestions(text: str) -> Tuple[str, List[str]]:
    """Transliterate and return suggestions."""
    return get_transliterator().transliterate_with_suggestions(text)


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
