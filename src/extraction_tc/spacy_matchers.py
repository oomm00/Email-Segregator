import logging

logger = logging.getLogger(__name__)

_spacy = None
_nlp = None


def _ensure_spacy():
    global _spacy, _nlp
    if _nlp is not None:
        return
    try:
        import spacy
        _nlp = spacy.load("en_core_web_sm", disable=["lemmatizer", "parser"])
        _spacy = spacy

        from spacy.matcher import Matcher
        matcher = Matcher(_nlp.vocab)

        # LABELED_VESSEL: "VESSEL: Some Name"
        matcher.add("LABELED_VESSEL", [
            [{"LOWER": "vessel"}, {"ORTH": ":"}, {"IS_ALPHA": True, "IS_TITLE": True}, {"IS_ALPHA": True, "IS_TITLE": True, "OP": "*"}],
        ])

        # MV_VESSEL: "M/V Ocean Star" or "MV Ocean Star"
        matcher.add("MV_VESSEL", [
            [{"LOWER": {"IN": ["m/v", "mv", "m.v", "motor"]}}, {"IS_ALPHA": True, "IS_TITLE": True}, {"IS_ALPHA": True, "IS_TITLE": True, "OP": "*"}],
        ])

        # LABELED_ACCOUNT: "ACCOUNT: Name" or "CHARTERER: Name"
        matcher.add("LABELED_ACCOUNT", [
            [{"LOWER": {"IN": ["account", "acct", "charterer", "owner", "owners"]}}, {"ORTH": ":"}, {"IS_ALPHA": True, "IS_TITLE": True}, {"IS_ALPHA": True, "IS_TITLE": True, "OP": "*"}],
        ])

        # DELIVERY_PORT: "DELIVERY: Port" or "DELIVERY PORT: Port"
        matcher.add("DELIVERY_PORT", [
            [{"LOWER": {"IN": ["delivery", "delivered"]}}, {"ORTH": ":"}, {"IS_TITLE": True, "IS_ALPHA": True}, {"IS_TITLE": True, "IS_ALPHA": True, "OP": "*"}],
        ])

        # REDELIVERY_PORT: "REDELIVERY: Port" or "REDEL: Port"
        matcher.add("REDELIVERY_PORT", [
            [{"LOWER": {"IN": ["redelivery", "redel", "redelivered"]}}, {"ORTH": ":"}, {"IS_TITLE": True, "IS_ALPHA": True}, {"IS_TITLE": True, "IS_ALPHA": True, "OP": "*"}],
        ])

        # HIRE_RATE: "HIRE: 12500"
        matcher.add("HIRE_RATE", [
            [{"LOWER": {"IN": ["hire", "rate", "hire rate"]}}, {"ORTH": ":"}, {"LIKE_NUM": True}],
        ])

        # DWT: "DWT: 82000"
        matcher.add("DWT_SIZE", [
            [{"LOWER": {"IN": ["dwt", "deadweight"]}}, {"ORTH": ":"}, {"LIKE_NUM": True}],
        ])

        # COMMISSION_PCT: "COM: 1.25"
        matcher.add("COMMISSION_PCT", [
            [{"LOWER": {"IN": ["com", "comm", "commission", "brokerage", "ttl"]}}, {"ORTH": ":"}, {"LIKE_NUM": True}],
        ])

        # INTENDED_CARGO: "CARGO: Grains"
        matcher.add("INTENDED_CARGO", [
            [{"LOWER": {"IN": ["cargo", "commodity", "trade"]}}, {"ORTH": ":"}, {"IS_TITLE": True, "IS_ALPHA": True}, {"IS_TITLE": True, "IS_ALPHA": True, "OP": "*"}],
        ])

        _nlp.matcher = matcher

    except ImportError:
        logger.warning("spaCy not available; TC matchers disabled")
        _nlp = None
        _spacy = None


def extract_spacy_tc(text: str) -> dict:
    _ensure_spacy()
    result = {}
    if _nlp is None or not text.strip():
        return result

    doc = _nlp(text)

    # Matcher patterns
    if hasattr(_nlp, "matcher"):
        matches = _nlp.matcher(doc)
        for match_id, start, end in matches:
            label = _nlp.vocab.strings[match_id]
            span = doc[start:end]
            val = span.text.strip()
            if ":" in val:
                val = val.split(":", 1)[-1].strip()
            if not val:
                continue
            key_map = {
                "LABELED_VESSEL": "vessel_name",
                "MV_VESSEL": "vessel_name",
                "LABELED_ACCOUNT": "account_name",
                "DELIVERY_PORT": "delivery_port",
                "REDELIVERY_PORT": "redelivery_port",
                "HIRE_RATE": "hire_rate",
                "DWT_SIZE": "vessel_dwt",
                "COMMISSION_PCT": "commission_pct",
                "INTENDED_CARGO": "intended_cargo",
            }
            key = key_map.get(label)
            if key and key not in result:
                result[key] = (val, "spacy")

    # NER for GPE (ports), DATE (dates), ORG (accounts)
    for ent in doc.ents:
        if ent.label_ == "GPE" and ent.text.strip():
            if "delivery_port" not in result and any(
                t.lower_ in ("delivery", "delivered") for t in doc[max(0, ent.start - 3):ent.start]
            ):
                result["delivery_port"] = (ent.text.strip(), "spacy_gpe")
            if "redelivery_port" not in result and any(
                t.lower_ in ("redelivery", "redel", "redelivered") for t in doc[max(0, ent.start - 3):ent.start]
            ):
                result["redelivery_port"] = (ent.text.strip(), "spacy_gpe")
        if ent.label_ == "DATE" and ent.text.strip():
            if "delivery_date" not in result and any(
                t.lower_ in ("laycan", "laydown", "laying", "delivery", "cancel", "cancelling", "pwwd", "laydate")
                for t in doc[max(0, ent.start - 3):ent.start]
            ):
                result["delivery_date"] = (ent.text.strip(), "spacy_date")
            if "redelivery_date" not in result and any(
                t.lower_ in ("redelivery", "redel", "redelivered")
                for t in doc[max(0, ent.start - 3):ent.start]
            ):
                result["redelivery_date"] = (ent.text.strip(), "spacy_date")
        if ent.label_ == "ORG" and ent.text.strip():
            if "account_name" not in result and any(
                t.lower_ in ("account", "acct", "charterer", "owner", "owners")
                for t in doc[max(0, ent.start - 3):ent.start]
            ):
                result["account_name"] = (ent.text.strip(), "spacy")

    return result
