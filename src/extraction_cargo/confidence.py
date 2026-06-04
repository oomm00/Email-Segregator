from src.extraction_cargo.models import ExtractedField
from src.extraction_cargo.regex_patterns import KNOWN_CARGO_TYPES


def score_account_name(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy":
        return 0.7
    if method == "fallback":
        return 0.35
    return 0.5


def score_cargo_name(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy":
        return 0.7
    if method == "fallback":
        return 0.35
    return 0.5


def score_loading_port(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy_gpe":
        return 0.75
    if method == "fallback":
        return 0.3
    return 0.5


def score_discharge_port(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy_gpe":
        return 0.75
    if method == "fallback":
        return 0.3
    return 0.5


def score_laycan(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.95
    if method == "spacy_date":
        return 0.7
    if method == "fallback":
        return 0.3
    return 0.5


def score_cargo_type(value: str, method: str) -> float:
    norm = value.strip().lower()
    exact = any(kt in norm for kt in KNOWN_CARGO_TYPES)
    if method == "regex_labeled" and exact:
        return 0.95
    if method == "regex_unlabeled" and exact:
        return 0.8
    if method == "spacy":
        return 0.65
    if method == "fallback":
        return 0.25
    return 0.5


def score_quantity(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "fallback":
        return 0.3
    return 0.5


def score_load_rate(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "fallback":
        return 0.3
    return 0.5


def score_discharge_rate(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "fallback":
        return 0.3
    return 0.5


def score_commission_pct(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "fallback":
        return 0.3
    return 0.5


def make_field(value: str, method: str, scorer) -> ExtractedField:
    cleaned = value.strip().rstrip(",").strip()
    if not cleaned:
        return ExtractedField(value="", confidence=0.0, method=method)
    conf = scorer(cleaned, method)
    return ExtractedField(value=cleaned, confidence=round(conf, 2), method=method)
