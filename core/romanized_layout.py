"""MPP Romanized keyboard layout mode (direct key -> character).

The OTHER romanized option: instead of phonetic transliteration
("namaste" -> "नमस्ते"), each key always yields the same character
("k" -> "क", "a" -> "ा"). This is the Madan Puraskar Pustakalaya (MPP)
Romanized standard shipped on Windows/macOS/Linux.

Mapping ported from Keyman `nepali_romanized.kmn` v1.0.1
(MIT-licensed keymanapp/keyboards repo; reference copy vendored at
tools/reference/nepali_romanized.kmn). Verified 1:1 by
tests/test_layouts.py::test_romanized_parity_with_kmn.

Note: asheshwor's Windows MSKLC build of the same MPP standard agrees on
every base/shift key except backslash (klc: literal \\ and |, kmn: ॐ and ः)
and adds an AltGr bonus layer. This module follows the Keyman table.
"""

ROMANIZED_MAP = {
    # digits
    "0": "०", "1": "१", "2": "२", "3": "३", "4": "४",
    "5": "५", "6": "६", "7": "७", "8": "८", "9": "९",
    # lowercase
    "a": "ा", "b": "ब", "c": "च", "d": "द", "e": "े",
    "f": "उ", "g": "ग", "h": "ह", "i": "ि", "j": "ज",
    "k": "क", "l": "ल", "m": "म", "n": "न", "o": "ो",
    "p": "प", "q": "ट", "r": "र", "s": "स", "t": "त",
    "u": "ु", "v": "व", "w": "ौ", "x": "ड", "y": "य",
    "z": "ष",
    # uppercase (shift)
    "A": "आ", "B": "भ", "C": "छ", "D": "ध", "E": "ै",
    "F": "ऊ", "G": "घ", "H": "अ", "I": "ी", "J": "झ",
    "K": "ख", "L": "॥", "M": "ं", "N": "ण", "O": "ओ",
    "P": "फ", "Q": "ठ", "R": "ृ", "S": "श", "T": "थ",
    "U": "ू", "V": "ँ", "W": "औ", "X": "ढ", "Y": "ञ",
    "Z": "ऋ",
    # symbols (shift pairs produce ASCII as in the kmn, except noted)
    "~": "ऽ", "`": "़", "!": "!", "@": "@", "#": "#",
    "$": "$", "%": "%", "^": "^", "&": "&", "*": "*",
    "(": "(", ")": ")", "-": "-", "_": "_", "+": "\u200c",
    "=": "‍", "[": "इ", "]": "ए", "{": "ई", "}": "ऐ",
    # NOTE: the kmn writes the double-quote key single-quoted ('"') mapping
    # to itself — identical to passthrough, kept explicit for parity.
    ";": ";", ":": ":", "'": "'", '"': '"', ",": ",",
    "<": "ङ", ".": "।", ">": ".", "/": "्", "?": "?",
    "\\": "ॐ", "|": "ः",
}

LAYOUT_NAME = "romanized-mpp"
LAYOUT_SOURCE = "Keyman nepali_romanized.kmn v1.0.1 (MPP Romanized)"


def romanized_type(text: str) -> str:
    """Map each character through the MPP Romanized layout (passthrough unknown)."""
    return "".join(ROMANIZED_MAP.get(ch, ch) for ch in text)
