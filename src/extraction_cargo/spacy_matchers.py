import logging

import spacy
from spacy.matcher import Matcher

logger = logging.getLogger(__name__)

_nlp = None


def _get_nlp():
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.info("downloading spaCy model en_core_web_sm")
            import subprocess
            subprocess.run(["python", "-m", "spacy", "download", "en_core_web_sm"], check=True)
            _nlp = spacy.load("en_core_web_sm")
    return _nlp


def _build_matcher(nlp):
    matcher = Matcher(nlp.vocab)
    # Cargo name after CARGO label
    matcher.add("LABELED_CARGO", [
        [{"LOWER": {"IN": ["cargo", "commodity", "product"]}},
         {"IS_PUNCT": True, "OP": "?"},
         {"IS_ALPHA": True, "IS_TITLE": True, "OP": "+"}],
    ])
    # Account after ACCOUNT/CHARTERER label
    matcher.add("LABELED_ACCOUNT", [
        [{"LOWER": {"IN": ["account", "acct", "charterer", "owner"]}},
         {"IS_PUNCT": True, "OP": "?"},
         {"IS_ALPHA": True, "IS_TITLE": True, "OP": "+"}],
    ])
    # Quantity pattern: number + MT/KMT
    matcher.add("CARGO_QTY", [
        [{"LIKE_NUM": True}, {"LOWER": {"IN": ["mt", "kmt", "tons", "tonnes"]}}],
    ])
    # Loading rate with PWWD/SSHEX
    matcher.add("LOAD_RATE", [
        [{"LIKE_NUM": True}, {"LOWER": "mt", "OP": "?"},
         {"IS_PUNCT": True, "OP": "*"},
         {"LOWER": {"IN": ["pwwd", "sshex", "shinc", "shex"]}, "OP": "?"}],
    ])
    return matcher


def extract_with_spacy(text: str) -> dict:
    nlp = _get_nlp()
    doc = nlp(text)
    matcher = _build_matcher(nlp)
    matches = matcher(doc)

    results = {
        "cargo_name": None, "account_name": None,
        "quantity": None, "load_rate": None,
        "loading_port": None, "discharge_port": None,
        "laycan": None, "cargo_type": None,
    }

    for match_id, start, end in matches:
        span = doc[start:end]
        label = nlp.vocab[match_id].text
        if label == "LABELED_CARGO":
            val = " ".join([t.text for t in doc[start + 1:end] if not t.is_punct])
            if val and not results["cargo_name"]:
                results["cargo_name"] = val
        elif label == "LABELED_ACCOUNT":
            val = " ".join([t.text for t in doc[start + 1:end] if not t.is_punct])
            if val and not results["account_name"]:
                results["account_name"] = val
        elif label == "CARGO_QTY" and end - start >= 2:
            if not results["quantity"]:
                results["quantity"] = doc[start].text
        elif label == "LOAD_RATE":
            if not results["load_rate"]:
                results["load_rate"] = doc[start].text

    # Named entity extraction for ports and dates and types
    for ent in doc.ents:
        if ent.label_ == "GPE":
            if not results.get("loading_port"):
                results["loading_port"] = ent.text
            elif not results.get("discharge_port") and ent.text != results["loading_port"]:
                results["discharge_port"] = ent.text
        elif ent.label_ == "DATE" and not results.get("laycan"):
            results["laycan"] = ent.text
        elif ent.label_ == "ORG" and not results.get("account_name"):
            if not results["account_name"]:
                results["account_name"] = ent.text

    return results
