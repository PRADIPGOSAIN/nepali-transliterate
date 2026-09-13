"""Traditional Nepali keyboard layout mode (direct key -> character).

While romanized mode transliterates phonetics ("namaste" -> "नमस्ते"),
traditional mode maps each physical key straight to its Nepali character,
for typists trained on the standard Nepali Traditional keyboard
(MPP layout: "k" -> "प", "f" -> "ा", "l" -> "ि", ...).

Mapping ported from m17n `ne-trad.mim` (MPP traditional layout, LGPL —
combination with this GPL-2.0+ project is explicitly permitted by LGPL).
Verified 1:1 against the installed mim file by
tests/test_traditional.py::test_parity_with_mim.
"""

TRAD_MAP = {
    # digits
    "0": "०", "1": "१", "2": "२", "3": "३", "4": "४",
    "5": "५", "6": "६", "7": "७", "8": "८", "9": "९",
    # lowercase row
    "a": "ब", "b": "द", "c": "अ", "d": "म", "e": "भ",
    "f": "ा", "g": "न", "h": "ज", "i": "ष", "j": "व",
    "k": "प", "l": "ि", "m": "ः", "n": "ल", "o": "य",
    "p": "उ", "q": "त्र", "r": "च", "s": "क", "t": "त",
    "u": "ग", "v": "ख", "w": "ध", "x": "ह", "y": "थ",
    "z": "श",
    # uppercase (shift) row
    "A": "आ", "B": "ौ", "C": "ऋ", "D": "ङ्ग", "E": "ऐ",
    "F": "ँ", "G": "द्द", "H": "झ", "I": "क्ष", "J": "ो",
    "K": "फ", "L": "ी", "M": "ड्ड", "N": "द्य", "O": "इ",
    "P": "ए", "Q": "त्त", "R": "द्ब", "S": "ङ्क", "T": "ट्ट",
    "U": "ऊ", "V": "ॐ", "W": "ड्ढ", "X": "ह्य", "Y": "ठ्ठ",
    "Z": "क्क",
    # punctuation / symbols
    ";": "स", ",": "ऽ", ".": "।", "/": "र",
    "'": "ु", '"': "ू", "`": "ञ", "~": "॥",
    "!": "ज्ञ", "@": "ई", "#": "घ", "$": "द्ध", "%": "छ",
    "^": "ट", "&": "ठ", "*": "ड", "(": "ढ", ")": "ण",
    "-": "औ", "_": "ओ", "=": "\u200d", "+": "\u200c",
    "[": "र्", "]": "े", "{": "ृ", "}": "ै",
    "|": "ं", "\\": "्", "?": "रु", ":": "ट्ठ", ">": "श्र",
    "<": "ङ",
}

LAYOUT_NAME = "traditional-mpp"
LAYOUT_SOURCE = "m17n ne-trad.mim (MPP traditional)"


def traditional_type(text: str) -> str:
    """Map each character through the traditional layout (passthrough unknown)."""
    return "".join(TRAD_MAP.get(ch, ch) for ch in text)


# Revision of the Traditional layout (Keyman nepali_traditional v1.3.1;
# reference vendored at tools/reference/nepali_traditional.kmn).
# Design changes vs the classic:
# caps row yields explicit half-consonants (S->क् not ङ्क), m is ZWNJ,
# "|" is ZWJ, "[" is ृ, "," stays a comma, "=" is a period, "~" is ऽ,
# and "{" starts a deadkey for literal ASCII (passed through here).
TRAD_KMN_MAP = {
    # digits
    "0": "०", "1": "१", "2": "२", "3": "३", "4": "४",
    "5": "५", "6": "६", "7": "७", "8": "८", "9": "९",
    # lowercase
    "a": "ब", "b": "द", "c": "अ", "d": "म", "e": "भ",
    "f": "ा", "g": "न", "h": "ज", "i": "ष", "j": "व",
    "k": "प", "l": "ि", "m": "\u200c", "n": "ल", "o": "य",
    "p": "उ", "q": "त्र", "r": "च", "s": "क", "t": "त",
    "u": "ग", "v": "ख", "w": "ध", "x": "ह", "y": "थ",
    "z": "श",
    # uppercase (shift): explicit half forms
    "A": "आ", "B": "ौ", "C": "ऋ", "D": "म्", "E": "ऐ",
    "F": "ँ", "G": "न्", "H": "झ", "I": "क्ष", "J": "ो",
    "K": "फ", "L": "ी", "M": "ः", "N": "ल्", "O": "इ",
    "P": "ए", "Q": "त्त", "R": "च्", "S": "क्", "T": "त्",
    "U": "ऊ", "V": "ॐ", "W": "ध्", "X": "ह्", "Y": "थ्",
    "Z": "श्",
    # symbols
    "~": "ऽ", "`": "ञ", "!": "ज्ञ", "@": "ई", "#": "घ",
    "$": "द्ध", "%": "छ", "^": "ट", "&": "ठ", "*": "ड",
    "(": "ढ", ")": "ण", "-": "औ", "_": "ओ", "+": "ं",
    "=": ".", "[": "ृ", "]": "े", "}": "ै",
    ";": "स", ":": "स्", "'": "ु", '"': "ू", ",": ",",
    "<": "ङ", ".": "।", ">": "श्र", "/": "र", "?": "?",
    "\\": "्", "|": "\u200d",
}

LAYOUT_KMN_NAME = "traditional-kmn-v1"
LAYOUT_KMN_SOURCE = "Keyman nepali_traditional.kmn v1.3.1"


def traditional_kmn_type(text: str) -> str:
    """Map each character through the revised Traditional layout."""
    return "".join(TRAD_KMN_MAP.get(ch, ch) for ch in text)
