"""nepali-transl package."""
from .nepali_transl import (
    NepaliTransliterator,
    get_transliterator,
    transliterate,
    transliterate_with_suggestions,
)
from .dictionary import WORD_CORRECTIONS, SUGGESTION_WORDS
from .preeti_bridge import preeti_to_unicode, detect_preeti  # optional backend
from .traditional import (TRAD_MAP, TRAD_KMN_MAP, traditional_type,
                          traditional_kmn_type, LAYOUT_NAME, LAYOUT_KMN_NAME)
from .romanized_layout import (ROMANIZED_MAP, romanized_type,
                               LAYOUT_NAME as ROMANIZED_LAYOUT_NAME)
try:
    from .words_auto import AUTO_CORRECTIONS  # generated (see tools/)
except ImportError:
    AUTO_CORRECTIONS = {}
try:
    from .words_suggest import ROMAN_SUGGESTIONS  # generated (see tools/)
except ImportError:
    ROMAN_SUGGESTIONS = []

__version__ = "0.14.0"
__all__ = [
    "NepaliTransliterator",
    "get_transliterator",
    "transliterate",
    "transliterate_with_suggestions",
    "WORD_CORRECTIONS",
    "SUGGESTION_WORDS",
    "AUTO_CORRECTIONS",
    "ROMAN_SUGGESTIONS",
    "preeti_to_unicode",
    "detect_preeti",
    "TRAD_MAP",
    "TRAD_KMN_MAP",
    "traditional_type",
    "traditional_kmn_type",
    "LAYOUT_NAME",
    "LAYOUT_KMN_NAME",
    "ROMANIZED_MAP",
    "romanized_type",
    "ROMANIZED_LAYOUT_NAME",
]
