import logging
from typing import Optional

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
    # Vessel name after M/V or MV
    matcher.add("MV_VESSEL", [
        [{"LOWER": {"IN": ["mv", "m/v"]}},
         {"IS_ALPHA": True, "IS_TITLE": True, "OP": "+"}],
    ])
    # Vessel name after "VESSEL" label
    matcher.add("LABELED_VESSEL", [
        [{"LOWER": "vessel"}, {"IS_PUNCT": True, "OP": "?"},
         {"IS_ALPHA": True, "IS_TITLE": True, "OP": "+"}],
    ])
    # DWT pattern
    matcher.add("DWT_SIZE", [
        [{"LIKE_NUM": True}, {"LOWER": {"IN": ["dwt", "mt", "tons", "tonnes"]}}],
    ])
    # Ship type after TYPE label
    matcher.add("SHIP_TYPE", [
        [{"LOWER": "type"}, {"IS_PUNCT": True, "OP": "?"},
         {"IS_ALPHA": True, "IS_TITLE": True, "OP": "+"}],
    ])
    return matcher


def extract_with_spacy(text: str) -> dict:
    nlp = _get_nlp()
    doc = nlp(text)
    matcher = _build_matcher(nlp)
    matches = matcher(doc)

    spacy_results = {"vessel_name": None, "vessel_type": None, "vessel_size_dwt": None}

    for match_id, start, end in matches:
        span = doc[start:end]
        label = nlp.vocab[match_id].text
        if label == "MV_VESSEL" and end - start >= 2:
            name = " ".join([t.text for t in doc[start + 1:end]])
            if name and not spacy_results["vessel_name"]:
                spacy_results["vessel_name"] = name
        elif label == "LABELED_VESSEL":
            name = " ".join([t.text for t in doc[start + 1:end] if not t.is_punct])
            if name and not spacy_results["vessel_name"]:
                spacy_results["vessel_name"] = name
        elif label == "DWT_SIZE" and end - start >= 2:
            spacy_results["vessel_size_dwt"] = doc[start].text
        elif label == "SHIP_TYPE":
            t = " ".join([t.text for t in doc[start + 1:end] if not t.is_punct])
            if t:
                spacy_results["vessel_type"] = t

    # Named entity extraction for port and date
    for ent in doc.ents:
        if ent.label_ == "GPE" and not spacy_results.get("open_port"):
            spacy_results["open_port"] = ent.text
        elif ent.label_ == "DATE" and not spacy_results.get("open_date"):
            spacy_results["open_date"] = ent.text
        elif ent.label_ == "ORG" and not spacy_results.get("account_name"):
            spacy_results["account_name"] = ent.text

    return spacy_results
