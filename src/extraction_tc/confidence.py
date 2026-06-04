from src.extraction_tc.models import ExtractedField


def score_account_name(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy":
        return 0.7
    if method == "fallback":
        return 0.35
    return 0.5


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


def score_delivery_port(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy_gpe":
        return 0.75
    if method == "fallback":
        return 0.3
    return 0.5


def score_delivery_date(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.95
    if method == "spacy_date":
        return 0.7
    if method == "fallback":
        return 0.3
    return 0.5


def score_redelivery_port(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy_gpe":
        return 0.75
    if method == "fallback":
        return 0.3
    return 0.5


def score_redelivery_date(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "spacy_date":
        return 0.7
    if method == "fallback":
        return 0.3
    return 0.5


def score_charter_period(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "fallback":
        return 0.35
    return 0.5


def score_hire_rate(value: str, method: str) -> float:
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


def score_intended_cargo(value: str, method: str) -> float:
    if method == "regex_labeled":
        return 0.9
    if method == "fallback":
        return 0.35
    return 0.5


def score_vessel_dwt(value: str, method: str) -> float:
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
