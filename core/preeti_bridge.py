"""Optional Preeti (legacy ASCII font) -> Unicode bridge.

Preeti was the dominant Nepali typing font before Unicode. Lakhs of legacy
documents still exist in Preeti encoding. This module lets users migrate them
using this project as the single toolkit.

Design: the conversion table itself is NOT vendored here (upstream tables are
CC-BY-NC-SA licensed, incompatible with this project's GPL-2.0). Instead we
wrap the MIT-licensed PyPI package `preeti-unicode-converter`, which is an
optional dependency:

    pip install preeti-unicode-converter

Core transliteration (romanized -> Unicode) stays zero-dependency stdlib.
"""

_MISSING_MSG = (
    "Preeti conversion needs the optional package "
    "'preeti-unicode-converter' (MIT): pip install preeti-unicode-converter"
)


def is_available() -> bool:
    """True if the optional Preeti backend is installed."""
    try:
        import preeti_unicode  # noqa: F401
        return True
    except ImportError:
        return False


def preeti_to_unicode(text: str) -> str:
    """Convert Preeti-encoded text to Unicode Devanagari.

    Raises ImportError with install instructions if backend is missing.
    """
    try:
        from preeti_unicode import convert_text
    except ImportError as e:
        raise ImportError(_MISSING_MSG) from e
    return convert_text(text)


def detect_preeti(text: str) -> bool:
    """Heuristic: True if text looks like Preeti-encoded Nepali.

    Preeti text is plain ASCII with characteristic clusters (e.g. ']',
    '}', '{', 'f' matra usage) and almost no spaces-free long ASCII runs
    that would be English. This is a hint for UI file pickers, not proof.
    """
    if not text or not text.strip():
        return False
    ascii_letters = sum(1 for c in text if 'a' <= c <= 'z' or 'A' <= c <= 'Z')
    if ascii_letters < len(text) * 0.4:
        return False
    markers = set("]}{[f'/\\|~`")
    hits = sum(1 for c in text if c in markers)
    return hits >= max(2, len(text) // 60)
