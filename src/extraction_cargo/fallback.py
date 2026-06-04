import logging

from src.extraction_cargo.confidence import (
    make_field,
    score_account_name, score_cargo_name, score_loading_port,
    score_discharge_port, score_laycan, score_cargo_type,
    score_quantity, score_load_rate, score_discharge_rate,
    score_commission_pct,
)

logger = logging.getLogger(__name__)

_KNOWN_NOT_ACCOUNT = {
    "GOOD", "DAY", "PLEASE", "OFFER", "FIRM", "FOLL", "FULY", "PLS",
    "OUR", "CLOSE", "DIR", "CHRTRS", "DEAR", "SIRS", "HELLO", "HI",
    "SUBJECT", "RE", "FW", "FWD", "ATTN", "ATTENTION", "CC", "BCC",
    "DATED", "DATE", "TIME", "ESTIMATED", "ETA", "ETD",
    "CARGO", "COMMODITY", "PRODUCT", "LOAD", "DISCH", "PORT", "POL",
    "POD", "LP", "DP", "LAYCAN", "LAYDAYS", "PWWD", "CANCEL",
    "QUANTITY", "QTY", "TYPE", "COM", "COMM", "COMMISSION", "BROKERAGE",
    "TTL", "TOTAL", "RATE", "LOADRATE", "DISCHRATE", "FIOS", "FIOT",
    "CQD", "SHEX", "SSHEX", "SHINC", "PWWD", "FHINC",
    "MTS", "KMT", "TONS", "TONNES", "MT", "PCT",
    "ABT", "ABOUT", "APPROX", "MAX", "MIN", "MOLOO", "MOLOCHOPT",
    "JULY", "JUNE", "MAY", "APRIL", "MARCH", "AUGUST", "JANUARY",
    "FEBRUARY", "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER",
    "JAN", "FEB", "MAR", "APR", "JUN", "JUL", "AUG", "SEP", "OCT",
    "NOV", "DEC", "MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY",
    "FRIDAY", "SATURDAY", "SUNDAY",
}


def fallback_account_name(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(
        r'(?:ACCOUNT|ACCT|CHARTERER)\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)["\']?(?:\s*[,\)\n\r]|$)',
        text, re.I,
    )
    if m:
        val = m.group(1).strip().rstrip(",")
        if val:
            return val
    # first all-caps line that looks like a company name
    for line in text.split("\n"):
        line = line.strip()
        if not line or ":" in line or len(line) < 4 or len(line) > 60:
            continue
        if line.isupper():
            first = line.split()[0] if line.split() else ""
            if first in _KNOWN_NOT_ACCOUNT:
                continue
            # must look like a company name (no dates, no pure numbers)
            if not any(c.isdigit() for c in first):
                return line
    return None


def fallback_cargo_name(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(
        r'(?:CARGO|COMMODITY|PRODUCT)\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)]+?)["\']?(?:\s*[,\n\r]|$)',
        text, re.I,
    )
    if m:
        val = m.group(1).strip()
        if val:
            return val
    # unlabeled: first word after quantity+unit (stops at space or lowercase)
    m = re.search(r'\d[\d,\.]+(?:\s+\d{3})?\s*(?:MTS?|KMT|TONS?|TONNES?)\s+([A-Z][A-Z0-9/]+)', text, re.I)
    if m:
        return m.group(1).strip()
    return None


def _port_after_label(
    text: str,
    labels: list[str],
    existing: str | None,
) -> str | None:
    if existing:
        return existing
    import re
    pattern = r'(?:' + "|".join(labels) + r')\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)["\']?(?:\s*[,\n\r]|$)'
    m = re.search(pattern, text, re.I)
    if m:
        return m.group(1).strip()
    return None


def fallback_loading_port(text: str, existing: str | None) -> str | None:
    result = _port_after_label(text, ["LOAD PORT", "POL", "LP", "LOADING", "FROM"], existing)
    if result:
        return result
    # try "City / City" format on a line — first city is loading port
    if not existing:
        import re
        m = re.search(r'(?:^|\n)\s*([A-Z][A-Za-z \t\-\.]+)\s+/\s+([A-Z][A-Za-z \t\-\.]+)', text, re.I | re.M)
        if m:
            return m.group(1).strip()
    return None


def fallback_discharge_port(text: str, existing: str | None) -> str | None:
    result = _port_after_label(text, ["DISCHARGE PORT", "POD", "DP", "DISCH", "DEST", "TO"], existing)
    if result:
        return result
    # try "City / City" format on a line — second city is discharge port
    if not existing:
        import re
        m = re.search(r'(?:^|\n)\s*([A-Z][A-Za-z \t\-\.]+)\s+/\s+([A-Z][A-Za-z \t\-\.]+)', text, re.I | re.M)
        if m:
            return m.group(2).strip()
    return None


def fallback_laycan(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'(MID|FULL)\s+[A-Za-z]+\s+\d{4}', text, re.I)
    if m:
        return m.group(0).strip()
    m = re.search(r'(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+)', text)
    if m:
        return m.group(1).strip()
    return None


def fallback_cargo_type(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    from src.extraction_cargo.regex_patterns import CARGO_TYPE
    for pat in CARGO_TYPE:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    return None


def fallback_quantity(text: str, existing_min: str | None, existing_max: str | None) -> tuple[str | None, str | None]:
    if existing_min and existing_max:
        return existing_min, existing_max
    import re
    from src.extraction_cargo.regex_patterns import QUANTITY
    for pat in QUANTITY:
        m = pat.search(text)
        if m:
            g1 = m.group(1).strip() if m.group(1) else None
            g2 = m.group(2).strip() if m.lastindex and m.lastindex >= 2 and m.group(2) else None
            if g1:
                return g1, g2
    # fallback: any MT/KMT number not already captured
    m = re.search(r'(\d[\d,\.]*)\s*(?:MT|KMT|METRIC\s+TONS?)', text, re.I)
    if m:
        return m.group(1).strip(), None
    return None, None


def fallback_load_rate(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'(?:LOAD(?:ING)?\s+(?:RATE)?|LOADRATE)\s*[:#=]?\s*["\']?(\d[\d,\.]*)', text, re.I)
    if m:
        return m.group(1).strip()
    # unlabeled: "10000/12000" — take the first number as load rate
    m = re.search(r'(?:^|\n)\s*["\']?(\d{4,6})\s*\/\s*(\d{4,6})', text, re.M)
    if m:
        return m.group(1).strip()
    return None


def fallback_discharge_rate(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'(?:DISCH(?:ARGE)?\s+(?:RATE)?|DISCHRATE|UNLOAD(?:ING)?\s+RATE)\s*[:#=]?\s*["\']?(\d[\d,\.]*)', text, re.I)
    if m:
        return m.group(1).strip()
    # CQD
    if re.search(r'\bCQD\b', text, re.I):
        return "CQD"
    # unlabeled: "10000/12000" — take the second number as discharge rate
    m = re.search(r'(?:^|\n)\s*["\']?(\d{4,6})\s*\/\s*(\d{4,6})', text, re.M)
    if m:
        return m.group(2).strip()
    return None


def fallback_commission_pct(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    from src.extraction_cargo.regex_patterns import COMMISSION
    for pat in COMMISSION:
        m = pat.search(text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    # standalone percentage number
    m = re.search(r'(\d[\d,\.]*)\s*%', text)
    if m:
        return m.group(1).strip()
    # comma-as-decimal: "3,75% here" — replace comma with dot
    m = re.search(r'(\d+)[,](\d+)\s*%\s*(?:HERE|TTL|COM|COMM)?', text, re.I)
    if m:
        return m.group(1) + "." + m.group(2)
    return None
