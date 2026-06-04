import logging

from src.extraction_cargo.models import CargoVcExtraction, ExtractedField
from src.extraction_cargo.segmentation import segment_cargoes
from src.extraction_cargo.regex_patterns import (
    ACCOUNT_NAME, CARGO_NAME, LOADING_PORT, DISCHARGE_PORT,
    LAYCAN, CARGO_TYPE, QUANTITY, LOAD_RATE, DISCHARGE_RATE,
    COMMISSION, SPLIT_QTY_RANGE,
)
from src.extraction_cargo.confidence import (
    make_field,
    score_account_name, score_cargo_name, score_loading_port,
    score_discharge_port, score_laycan, score_cargo_type,
    score_quantity, score_load_rate, score_discharge_rate,
    score_commission_pct,
)
from src.extraction_cargo import fallback as fb
from src.extraction_cargo.validation import validate_extraction

logger = logging.getLogger(__name__)


def run_cargo_vc_pipeline(email_id: str, body_text: str, subject: str = "") -> list[CargoVcExtraction]:
    if not body_text:
        logger.warning("empty body for cargo vc email: %s", email_id)
        return []

    combined = f"{subject}\n{body_text}" if subject else body_text
    segments = segment_cargoes(combined)
    logger.info("segmented cargo vc email %s: %d segments", email_id, len(segments))

    results = []
    for idx, (seg_text, seg_conf) in enumerate(segments):
        extraction = _extract_single_cargo(seg_text, idx, seg_conf)
        if extraction.cargo_name:
            results.append(extraction)

    return results


def _extract_single_cargo(seg_text: str, index: int, seg_conf: float) -> CargoVcExtraction:
    raw = seg_text.strip()
    cargo = CargoVcExtraction(raw_text=raw, segment_index=index, segmentation_confidence=seg_conf)

    _extract_regex(raw, cargo)
    _extract_spacy(raw, cargo)
    _extract_fallback(raw, cargo)
    _post_process(cargo)

    return validate_extraction(cargo)


def _extract_regex(text: str, cargo: CargoVcExtraction) -> None:
    # account_name
    for pat in ACCOUNT_NAME:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.account_name = make_field(val, "regex_labeled", score_account_name)
                break

    # cargo_name
    for pat in CARGO_NAME:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.cargo_name = make_field(val, "regex_labeled", score_cargo_name)
                break

    # loading_port
    for pat in LOADING_PORT:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.loading_port = make_field(val, "regex_labeled", score_loading_port)
                break

    # discharge_port
    for pat in DISCHARGE_PORT:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.discharge_port = make_field(val, "regex_labeled", score_discharge_port)
                break

    # laycan
    for pat in LAYCAN:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.laycan = make_field(val, "regex_labeled", score_laycan)
                break

    # cargo_type
    for pat in CARGO_TYPE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.cargo_type = make_field(val, "regex_labeled", score_cargo_type)
                break

    # quantity
    for pat in QUANTITY:
        m = pat.search(text)
        if m:
            g1 = m.group(1).strip().rstrip(",") if m.group(1) else None
            g2 = m.group(2).strip().rstrip(",") if m.lastindex and m.lastindex >= 2 and m.group(2) else None
            g3 = m.group(3).strip().rstrip(",") if m.lastindex and m.lastindex >= 3 and m.group(3) else None

            # merge space-thousands (e.g. "20" + "000" -> "20,000")
            # only when g2 is 1-3 digit continuation, not a full number like "20,000"
            if g2 and not g3 and len(g2) <= 3 and g2.replace(",", "").isdigit():
                g1 = g1 + "," + g2 if "," not in g1 else g1 + g2
                g2 = None

            if g1 and not cargo.quantity_min_mt:
                cargo.quantity_min_mt = make_field(g1, "regex_labeled", score_quantity)
            if g3 and not cargo.quantity_max_mt:
                cargo.quantity_max_mt = make_field(g3, "regex_labeled", score_quantity)
            elif g2 and not cargo.quantity_max_mt:
                cargo.quantity_max_mt = make_field(g2, "regex_labeled", score_quantity)
            break

    # load_rate
    for pat in LOAD_RATE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.load_rate = make_field(val, "regex_labeled", score_load_rate)
                break

    # discharge_rate
    for pat in DISCHARGE_RATE:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.discharge_rate = make_field(val, "regex_labeled", score_discharge_rate)
                break

    # commission_pct
    for pat in COMMISSION:
        m = pat.search(text)
        if m:
            val = m.group(1).strip().rstrip(",").strip()
            if val:
                cargo.commission_pct = make_field(val, "regex_labeled", score_commission_pct)
                break


def _extract_spacy(text: str, cargo: CargoVcExtraction) -> None:
    try:
        from src.extraction_cargo.spacy_matchers import extract_with_spacy
        spacy_results = extract_with_spacy(text)
    except Exception as e:
        logger.warning("spacy extraction failed: %s", e)
        return

    if not cargo.cargo_name and spacy_results.get("cargo_name"):
        cargo.cargo_name = make_field(spacy_results["cargo_name"], "spacy", score_cargo_name)
    if not cargo.account_name and spacy_results.get("account_name"):
        cargo.account_name = make_field(spacy_results["account_name"], "spacy", score_account_name)
    if not cargo.loading_port and spacy_results.get("loading_port"):
        cargo.loading_port = make_field(spacy_results["loading_port"], "spacy_gpe", score_loading_port)
    if not cargo.discharge_port and spacy_results.get("discharge_port"):
        cargo.discharge_port = make_field(spacy_results["discharge_port"], "spacy_gpe", score_discharge_port)
    if not cargo.laycan and spacy_results.get("laycan"):
        cargo.laycan = make_field(spacy_results["laycan"], "spacy_date", score_laycan)
    if not cargo.cargo_type and spacy_results.get("cargo_type"):
        cargo.cargo_type = make_field(spacy_results["cargo_type"], "spacy", score_cargo_type)
    if not cargo.quantity_min_mt and spacy_results.get("quantity"):
        cargo.quantity_min_mt = make_field(spacy_results["quantity"], "spacy", score_quantity)
    if not cargo.load_rate and spacy_results.get("load_rate"):
        cargo.load_rate = make_field(spacy_results["load_rate"], "spacy", score_load_rate)


def _extract_fallback(text: str, cargo: CargoVcExtraction) -> None:
    existing = lambda f: f.value if f else None

    acct = fb.fallback_account_name(text, existing(cargo.account_name))
    if acct and not cargo.account_name:
        cargo.account_name = make_field(acct, "fallback", score_account_name)

    cname = fb.fallback_cargo_name(text, existing(cargo.cargo_name))
    if cname and not cargo.cargo_name:
        cargo.cargo_name = make_field(cname, "fallback", score_cargo_name)

    lport = fb.fallback_loading_port(text, existing(cargo.loading_port))
    if lport and not cargo.loading_port:
        cargo.loading_port = make_field(lport, "fallback", score_loading_port)

    dport = fb.fallback_discharge_port(text, existing(cargo.discharge_port))
    if dport and not cargo.discharge_port:
        cargo.discharge_port = make_field(dport, "fallback", score_discharge_port)

    date_ = fb.fallback_laycan(text, existing(cargo.laycan))
    if date_ and not cargo.laycan:
        cargo.laycan = make_field(date_, "fallback", score_laycan)

    tp = fb.fallback_cargo_type(text, existing(cargo.cargo_type))
    if tp and not cargo.cargo_type:
        cargo.cargo_type = make_field(tp, "fallback", score_cargo_type)

    qmin, qmax = fb.fallback_quantity(
        text,
        existing(cargo.quantity_min_mt),
        existing(cargo.quantity_max_mt),
    )
    if qmin and not cargo.quantity_min_mt:
        cargo.quantity_min_mt = make_field(qmin, "fallback", score_quantity)
    if qmax and not cargo.quantity_max_mt:
        cargo.quantity_max_mt = make_field(qmax, "fallback", score_quantity)

    lr = fb.fallback_load_rate(text, existing(cargo.load_rate))
    if lr and not cargo.load_rate:
        cargo.load_rate = make_field(lr, "fallback", score_load_rate)

    dr = fb.fallback_discharge_rate(text, existing(cargo.discharge_rate))
    if dr and not cargo.discharge_rate:
        cargo.discharge_rate = make_field(dr, "fallback", score_discharge_rate)

    com = fb.fallback_commission_pct(text, existing(cargo.commission_pct))
    if com and not cargo.commission_pct:
        cargo.commission_pct = make_field(com, "fallback", score_commission_pct)


def _post_process(cargo: CargoVcExtraction) -> None:
    # split quantity_min into min/max if it contains a range
    if cargo.quantity_min_mt and not cargo.quantity_max_mt:
        m = SPLIT_QTY_RANGE.search(cargo.quantity_min_mt.value)
        if m and m.lastindex and m.lastindex >= 2 and m.group(2):
            qmin = m.group(1).strip()
            qmax = m.group(2).strip()
            method = cargo.quantity_min_mt.method
            cargo.quantity_min_mt = make_field(qmin, method, score_quantity)
            cargo.quantity_max_mt = make_field(qmax, method, score_quantity)

    # expand abbreviated quantity like "20" -> "20,000" when paired with "30,000"
    if cargo.quantity_min_mt and cargo.quantity_max_mt:
        vmin = cargo.quantity_min_mt.value
        vmax = cargo.quantity_max_mt.value
        if "," not in vmin and "," in vmax:
            try:
                mins = float(vmin.replace(",", ""))
                maxs = float(vmax.replace(",", ""))
                if mins * 1000 <= maxs:
                    cargo.quantity_min_mt.value = vmin + ",000"
            except (ValueError, AttributeError):
                pass
