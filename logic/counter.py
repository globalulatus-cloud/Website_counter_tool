import re

def is_cjk(char: str) -> bool:
    """Check if a character is Chinese, Japanese, or Korean."""
    code = ord(char)
    # Common CJK Unicode ranges
    return (
        0x4E00 <= code <= 0x9FFF or   # Unified Ideographs
        0x3400 <= code <= 0x4DBF or   # Extension A
        0x3040 <= code <= 0x309F or   # Hiragana
        0x30A0 <= code <= 0x30FF or   # Katakana
        0xAC00 <= code <= 0xD7AF or   # Hangul Syllables
        0x1100 <= code <= 0x11FF or   # Hangul Jamo
        0xFF00 <= code <= 0xFFEF      # Halfwidth and Fullwidth Forms
    )

def count_stats(text: str):
    if not text:
        return {"type": "words", "count": 0, "language_group": "Latin"}

    # Filter out whitespace for character analysis
    clean_text = "".join(text.split())
    if not clean_text:
         return {"type": "words", "count": 0, "language_group": "Latin"}

    cjk_count = sum(1 for char in clean_text if is_cjk(char))
    cjk_ratio = cjk_count / len(clean_text)

    # Threshold: If more than 10% characters are CJK, treat as CJK
    if cjk_ratio > 0.1:
        return {
            "type": "characters",
            "count": len(clean_text),
            "language_group": "CJK",
            "cjk_ratio": round(cjk_ratio, 2)
        }
    else:
        # Latin/Word based
        words = text.split()
        return {
            "type": "words",
            "count": len(words),
            "language_group": "Latin"
        }
