import logging

logger = logging.getLogger(__name__)


def validate_tc_extraction(extraction) -> list[str]:
    warnings = []

    # delivery_date must contain 4-digit year
    dd = extraction.delivery_date
    if dd and dd.value:
        if not any(c.isdigit() for c in dd.value) or len(dd.value) < 4:
            warnings.append(f"delivery_date may be invalid: {dd.value}")
        elif not _has_four_digit_year(dd.value):
            warnings.append(f"delivery_date missing 4-digit year: {dd.value}")

    # redelivery_date must contain 4-digit year
    rd = extraction.redelivery_date
    if rd and rd.value:
        if not any(c.isdigit() for c in rd.value) or len(rd.value) < 4:
            warnings.append(f"redelivery_date may be invalid: {rd.value}")
        elif not _has_four_digit_year(rd.value):
            warnings.append(f"redelivery_date missing 4-digit year: {rd.value}")

    # commission 0-100%
    cp = extraction.commission_pct
    if cp and cp.value:
        try:
            val = float(cp.value.replace(",", ""))
            if val < 0 or val > 100:
                warnings.append(f"commission_pct out of range [0,100]: {cp.value}")
        except ValueError:
            warnings.append(f"commission_pct not numeric: {cp.value}")

    # hire_rate should be numeric
    hr = extraction.hire_rate
    if hr and hr.value:
        cleaned = hr.value.replace(",", "").replace("$", "").strip()
        try:
            float(cleaned)
        except ValueError:
            warnings.append(f"hire_rate not numeric: {hr.value}")

    # delivery_port and redelivery_port should not be identical
    dp = extraction.delivery_port
    rp = extraction.redelivery_port
    if dp and rp and dp.value and rp.value:
        if dp.value.strip().upper() == rp.value.strip().upper():
            warnings.append(f"delivery_port same as redelivery_port: {dp.value}")

    return warnings


def _has_four_digit_year(val: str) -> bool:
    import re
    return bool(re.search(r'\b(19|20)\d{2}\b', val))
