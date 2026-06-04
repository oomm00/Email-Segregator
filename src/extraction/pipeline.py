import logging

from src.extraction.models import VesselExtraction, ExtractedField
from src.extraction.segmentation import segment_vessels
from src.extraction.regex_patterns import (
    VESSEL_NAME, ACCOUNT_NAME, OPEN_PORT, OPEN_DATE,
    VESSEL_TYPE, VESSEL_SIZE_DWT,
)
from src.extraction.confidence import (
    make_field,
    score_vessel_name, score_account_name, score_open_port,
    score_open_date, score_vessel_type, score_vessel_size_dwt,
)
from src.extraction import fallback as fb

logger = logging.getLogger(__name__)


def run_tonnage_pipeline(email_id: str, body_text: str, subject: str = "") -> list[VesselExtraction]:
    if not body_text:
        logger.warning("empty body for tonnage email: %s", email_id)
        return []

    combined = f"{subject}\n{body_text}" if subject else body_text
    segments = segment_vessels(combined)
    logger.info("segmented tonnage email %s: %d segments", email_id, len(segments))

    seen_names = set()
    results = []
    for idx, (seg_text, seg_conf) in enumerate(segments):
        extraction = _extract_single_vessel(seg_text, idx, seg_conf)
        if extraction.vessel_name:
            name = extraction.vessel_name.value.strip().upper()
            if name and name not in seen_names:
                seen_names.add(name)
                results.append(extraction)

    return results


def _extract_single_vessel(seg_text: str, index: int, seg_conf: float) -> VesselExtraction:
    raw = seg_text.strip()
    vessel = VesselExtraction(raw_text=raw, segment_index=index, segmentation_confidence=seg_conf)

    _extract_regex(raw, vessel)
    _extract_spacy(raw, vessel)
    _extract_fallback(raw, vessel)

    return vessel


def _extract_regex(text: str, vessel: VesselExtraction) -> None:
    # vessel_name
    for pat in VESSEL_NAME:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                method = "regex_labeled" if pat.pattern.startswith(("VESSEL", "VSL")) else "regex_marker"
                vessel.vessel_name = make_field(val, method, score_vessel_name)
                break

    # account_name
    for pat in ACCOUNT_NAME:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                vessel.account_name = make_field(val, "regex_labeled", score_account_name)
                break

    # open_port
    for pat in OPEN_PORT:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                vessel.open_port = make_field(val, "regex_labeled", score_open_port)
                break

    # open_date
    for pat in OPEN_DATE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                vessel.open_date = make_field(val, "regex_labeled", score_open_date)
                break

    # vessel_type
    for pat in VESSEL_TYPE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                method = "regex_labeled" if pat.pattern.startswith(r'(?:TYPE') else "regex_unlabeled"
                vessel.vessel_type = make_field(val, method, score_vessel_type)
                break

    # vessel_size_dwt
    for pat in VESSEL_SIZE_DWT:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                method = "regex_labeled" if pat.pattern.startswith(r'(?:DWT|DEADWEIGHT') else "regex_marker"
                vessel.vessel_size_dwt = make_field(val, method, score_vessel_size_dwt)
                break


def _extract_spacy(text: str, vessel: VesselExtraction) -> None:
    try:
        from src.extraction.spacy_matchers import extract_with_spacy
        spacy_results = extract_with_spacy(text)
    except Exception as e:
        logger.warning("spacy extraction failed: %s", e)
        return

    if not vessel.vessel_name and spacy_results.get("vessel_name"):
        vessel.vessel_name = make_field(spacy_results["vessel_name"], "spacy", score_vessel_name)
    if not vessel.vessel_type and spacy_results.get("vessel_type"):
        vessel.vessel_type = make_field(spacy_results["vessel_type"], "spacy", score_vessel_type)
    if not vessel.vessel_size_dwt and spacy_results.get("vessel_size_dwt"):
        vessel.vessel_size_dwt = make_field(spacy_results["vessel_size_dwt"], "spacy", score_vessel_size_dwt)
    if not vessel.open_port and spacy_results.get("open_port"):
        vessel.open_port = make_field(spacy_results["open_port"], "spacy_gpe", score_open_port)
    if not vessel.open_date and spacy_results.get("open_date"):
        val = spacy_results["open_date"]
        # spaCy sometimes mislabels numeric values as dates; skip pure numbers
        if not val.replace(",", "").replace(".", "").isdigit():
            vessel.open_date = make_field(val, "spacy_date", score_open_date)
    if not vessel.account_name and spacy_results.get("account_name"):
        vessel.account_name = make_field(spacy_results["account_name"], "spacy", score_account_name)


def _extract_fallback(text: str, vessel: VesselExtraction) -> None:
    existing_name = vessel.vessel_name.value if vessel.vessel_name else None

    name = fb.fallback_vessel_name(text, existing_name)
    if name and not vessel.vessel_name:
        vessel.vessel_name = make_field(name, "fallback", score_vessel_name)

    acct = fb.fallback_account_name(text, vessel.account_name.value if vessel.account_name else None)
    if acct and not vessel.account_name:
        vessel.account_name = make_field(acct, "fallback", score_account_name)

    port = fb.fallback_open_port(text, vessel.open_port.value if vessel.open_port else None)
    if port and not vessel.open_port:
        vessel.open_port = make_field(port, "fallback", score_open_port)

    date_ = fb.fallback_open_date(text, vessel.open_date.value if vessel.open_date else None)
    if date_ and not vessel.open_date:
        vessel.open_date = make_field(date_, "fallback", score_open_date)

    tp = fb.fallback_vessel_type(text, vessel.vessel_type.value if vessel.vessel_type else None)
    if tp and not vessel.vessel_type:
        vessel.vessel_type = make_field(tp, "fallback", score_vessel_type)

    dwt = fb.fallback_vessel_size_dwt(text, vessel.vessel_size_dwt.value if vessel.vessel_size_dwt else None)
    if dwt and not vessel.vessel_size_dwt:
        vessel.vessel_size_dwt = make_field(dwt, "fallback", score_vessel_size_dwt)
