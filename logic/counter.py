import re


def detect_language_group(text: str) -> str:
    if not text:
        return "Latin"

    cjk_count = len(re.findall(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]", text))
    latin_count = len(re.findall(r"[A-Za-z]", text))

    if cjk_count > latin_count:
        return "CJK"
    return "Latin"


def count_stats(text: str) -> dict:
    if not text:
        return {
            "count": 0,
            "type": "words",
            "language_group": "Latin",
        }

    text = re.sub(r"\s+", " ", text).strip()
    language_group = detect_language_group(text)

    if language_group == "CJK":
        count = len(re.sub(r"\s+", "", text))
        return {
            "count": count,
            "type": "chars",
            "language_group": language_group,
        }

    words = re.findall(r"\b[\w'-]+\b", text, flags=re.UNICODE)
    return {
        "count": len(words),
        "type": "words",
        "language_group": language_group,
    }
