from src.extraction.models import ExtractedField
from src.extraction.regex_patterns import KNOWN_VESSEL_TYPES


def score_vessel_name(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.95
    if method == "regex_marker":
        return 0.85
    if method == "spacy":
        return 0.75
    if method == "fallback":
        return 0.4
    return 0.5


def score_account_name(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "regex_marker":
        return 0.8
    if method == "spacy":
        return 0.7
    if method == "fallback":
        return 0.35
    return 0.5


def score_open_port(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy_gpe":
        return 0.75
    if method == "fallback":
        return 0.3
    return 0.5


def score_open_date(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.95
    if method == "spacy_date":
        return 0.7
    if method == "fallback":
        return 0.3
    return 0.5


def score_vessel_type(value: str, method: str) -> float:
    norm = value.strip().lower()
    exact = norm in KNOWN_VESSEL_TYPES
    if method == "regex_labeled" and exact:
        return 0.95
    if method == "regex_unlabeled" and exact:
        return 0.8
    if method == "spacy":
        return 0.65
    if method == "fallback":
        return 0.25
    return 0.5


def score_vessel_size_dwt(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.95
    if method == "regex_marker":
        return 0.85
    if method == "fallback":
        return 0.3
    return 0.5


def make_field(value: str, method: str, scorer) -> ExtractedField:
    cleaned = value.strip().rstrip(",").strip()
    if not cleaned:
        return ExtractedField(value="", confidence=0.0, method=method)
    conf = scorer(cleaned, method)
    return ExtractedField(value=cleaned, confidence=round(conf, 2), method=method)
