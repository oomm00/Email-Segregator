import logging

from src.extraction_tc.models import TcExtraction, ExtractedField
from src.extraction_tc.regex_patterns import (
    ACCOUNT_NAME, VESSEL_NAME, DELIVERY_PORT, DELIVERY_DATE,
    REDELIVERY_PORT, REDELIVERY_DATE, CHARTER_PERIOD, HIRE_RATE,
    COMMISSION, INTENDED_CARGO, VESSEL_DWT,
)
from src.extraction_tc.segmentation import segment_tc_vessels
from src.extraction_tc import fallback as fb
from src.extraction_tc.confidence import (
    make_field,
    score_account_name, score_vessel_name,
    score_delivery_port, score_delivery_date,
    score_redelivery_port, score_redelivery_date,
    score_charter_period, score_hire_rate,
    score_commission_pct, score_intended_cargo,
    score_vessel_dwt,
)
from src.extraction_tc.validation import validate_tc_extraction

logger = logging.getLogger(__name__)


def run_tc_pipeline(email_id: str, body_text: str, subject: str = "") -> list[TcExtraction]:
    if not body_text:
        logger.warning("empty body for tc email: %s", email_id)
        return []

    combined = f"{subject}\n{body_text}" if subject else body_text
    segments = segment_tc_vessels(combined)
    logger.info("segmented tc email %s: %d segments", email_id, len(segments))

    results = []
    for idx, seg in enumerate(segments):
        seg_conf = 1.0 / (1 + idx * 0.1) if len(segments) > 1 else 1.0
        extraction = _extract_single_tc(seg, idx, seg_conf)
        if extraction.vessel_name or extraction.account_name or extraction.intended_cargo:
            results.append(extraction)

    return results


def _extract_single_tc(seg_text: str, index: int, seg_conf: float) -> TcExtraction:
    raw = seg_text.strip()
    tc = TcExtraction(raw_text=raw, segment_index=index, segmentation_confidence=seg_conf)

    _extract_regex(raw, tc)
    _extract_spacy(raw, tc)
    _extract_fallback(raw, tc)

    warnings = validate_tc_extraction(tc)
    if warnings:
        for w in warnings:
            logger.warning("TC validation [seg %d]: %s", index, w)

    return tc


def _extract_regex(text: str, tc: TcExtraction) -> None:
    for pat in ACCOUNT_NAME:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.account_name = make_field(val, "regex_labeled", score_account_name)
                break

    for pat in VESSEL_NAME:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                method = "regex_labeled" if pat.pattern.startswith("(?:M/V|MV|MOTOR") else "regex_marker"
                tc.vessel_name = make_field(val, method, score_vessel_name)
                break

    for pat in DELIVERY_PORT:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            val = fb.strip_port_qualifier(val)
            if val:
                tc.delivery_port = make_field(val, "regex_labeled", score_delivery_port)
                break

    for pat in DELIVERY_DATE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.delivery_date = make_field(val, "regex_labeled", score_delivery_date)
                break

    for pat in REDELIVERY_PORT:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            val = fb.strip_port_qualifier(val)
            if val:
                tc.redelivery_port = make_field(val, "regex_labeled", score_redelivery_port)
                break

    for pat in REDELIVERY_DATE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.redelivery_date = make_field(val, "regex_labeled", score_redelivery_date)
                break

    for pat in CHARTER_PERIOD:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.charter_period = make_field(val, "regex_labeled", score_charter_period)
                break

    for pat in HIRE_RATE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.hire_rate = make_field(val, "regex_labeled", score_hire_rate)
                break

    for pat in COMMISSION:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.commission_pct = make_field(val, "regex_labeled", score_commission_pct)
                break

    for pat in INTENDED_CARGO:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.intended_cargo = make_field(val, "regex_labeled", score_intended_cargo)
                break

    for pat in VESSEL_DWT:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                tc.vessel_dwt = make_field(val, "regex_labeled", score_vessel_dwt)
                break


def _extract_spacy(text: str, tc: TcExtraction) -> None:
    try:
        from src.extraction_tc.spacy_matchers import extract_spacy_tc
        spacy_results = extract_spacy_tc(text)
    except Exception as e:
        logger.warning("spacy extraction failed: %s", e)
        return

    if not tc.vessel_name and spacy_results.get("vessel_name"):
        tc.vessel_name = make_field(spacy_results["vessel_name"][0], "spacy", score_vessel_name)
    if not tc.account_name and spacy_results.get("account_name"):
        tc.account_name = make_field(spacy_results["account_name"][0], "spacy", score_account_name)
    if not tc.delivery_port and spacy_results.get("delivery_port"):
        tc.delivery_port = make_field(spacy_results["delivery_port"][0], "spacy_gpe", score_delivery_port)
    if not tc.redelivery_port and spacy_results.get("redelivery_port"):
        tc.redelivery_port = make_field(spacy_results["redelivery_port"][0], "spacy_gpe", score_redelivery_port)
    if not tc.delivery_date and spacy_results.get("delivery_date"):
        tc.delivery_date = make_field(spacy_results["delivery_date"][0], "spacy_date", score_delivery_date)
    if not tc.redelivery_date and spacy_results.get("redelivery_date"):
        tc.redelivery_date = make_field(spacy_results["redelivery_date"][0], "spacy_date", score_redelivery_date)
    if not tc.charter_period and spacy_results.get("charter_period"):
        tc.charter_period = make_field(spacy_results["charter_period"][0], "spacy", score_charter_period)
    if not tc.hire_rate and spacy_results.get("hire_rate"):
        tc.hire_rate = make_field(spacy_results["hire_rate"][0], "spacy", score_hire_rate)
    if not tc.vessel_dwt and spacy_results.get("vessel_dwt"):
        tc.vessel_dwt = make_field(spacy_results["vessel_dwt"][0], "spacy", score_vessel_dwt)
    if not tc.commission_pct and spacy_results.get("commission_pct"):
        tc.commission_pct = make_field(spacy_results["commission_pct"][0], "spacy", score_commission_pct)
    if not tc.intended_cargo and spacy_results.get("intended_cargo"):
        tc.intended_cargo = make_field(spacy_results["intended_cargo"][0], "spacy", score_intended_cargo)


def _extract_fallback(text: str, tc: TcExtraction) -> None:
    existing = lambda f: f.value if f else None

    acct = fb.fallback_account_name(text, existing(tc.account_name))
    if acct and not tc.account_name:
        tc.account_name = make_field(acct, "fallback", score_account_name)

    vname = fb.fallback_vessel_name(text, existing(tc.vessel_name))
    if vname and not tc.vessel_name:
        tc.vessel_name = make_field(vname, "fallback", score_vessel_name)

    dport = fb.fallback_delivery_port(text, existing(tc.delivery_port))
    if dport and not tc.delivery_port:
        dport = fb.strip_port_qualifier(dport)
        if dport:
            tc.delivery_port = make_field(dport, "fallback", score_delivery_port)

    ddate = fb.fallback_delivery_date(text, existing(tc.delivery_date))
    if ddate and not tc.delivery_date:
        tc.delivery_date = make_field(ddate, "fallback", score_delivery_date)

    rport = fb.fallback_redelivery_port(text, existing(tc.redelivery_port))
    if rport and not tc.redelivery_port:
        rport = fb.strip_port_qualifier(rport)
        if rport:
            tc.redelivery_port = make_field(rport, "fallback", score_redelivery_port)

    rdate = fb.fallback_redelivery_date(text, existing(tc.redelivery_date))
    if rdate and not tc.redelivery_date:
        tc.redelivery_date = make_field(rdate, "fallback", score_redelivery_date)

    p = fb.fallback_charter_period(text, existing(tc.charter_period))
    if p and not tc.charter_period:
        tc.charter_period = make_field(p, "fallback", score_charter_period)

    hr = fb.fallback_hire_rate(text, existing(tc.hire_rate))
    if hr and not tc.hire_rate:
        tc.hire_rate = make_field(hr, "fallback", score_hire_rate)

    cp = fb.fallback_commission_pct(text, existing(tc.commission_pct))
    if cp and not tc.commission_pct:
        tc.commission_pct = make_field(cp, "fallback", score_commission_pct)

    ic = fb.fallback_intended_cargo(text, existing(tc.intended_cargo))
    if ic and not tc.intended_cargo:
        tc.intended_cargo = make_field(ic, "fallback", score_intended_cargo)

    dwt = fb.fallback_vessel_dwt(text, existing(tc.vessel_dwt))
    if dwt and not tc.vessel_dwt:
        tc.vessel_dwt = make_field(dwt, "fallback", score_vessel_dwt)
