"""nepali-transl package."""
from .nepali_transl import (
    NepaliTransliterator,
    get_transliterator,
    transliterate,
    transliterate_with_suggestions,
)
from .dictionary import WORD_CORRECTIONS, SUGGESTION_WORDS
from .preeti_bridge import preeti_to_unicode, detect_preeti  # optional backend
from .traditional import TRAD_MAP, traditional_type, LAYOUT_NAME
try:
    from .words_suggest import ROMAN_SUGGESTIONS  # generated (see tools/)
except ImportError:
    ROMAN_SUGGESTIONS = []

__version__ = "0.10.0"
__all__ = [
    "NepaliTransliterator",
    "get_transliterator",
    "transliterate",
    "transliterate_with_suggestions",
    "WORD_CORRECTIONS",
    "SUGGESTION_WORDS",
    "ROMAN_SUGGESTIONS",
    "preeti_to_unicode",
    "detect_preeti",
    "TRAD_MAP",
    "traditional_type",
    "LAYOUT_NAME",
]
