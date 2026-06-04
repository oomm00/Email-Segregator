import logging
import re

from src.extraction_tc.regex_patterns import VESSEL_NAME, COMMISSION
from src.extraction_tc.confidence import (
    make_field,
    score_account_name, score_vessel_name, score_delivery_port,
    score_delivery_date, score_redelivery_port, score_redelivery_date,
    score_charter_period, score_hire_rate, score_commission_pct,
    score_intended_cargo, score_vessel_dwt,
)

logger = logging.getLogger(__name__)

_PORT_QUALIFIERS = re.compile(
    r'^(?:TM|BERTH|ANCHORAGE|ANCH|SPOT|TO\s+MAKE)\s+',
    re.I,
)
_PAREN_ANNOT = re.compile(r'\s*\([^)]*\)')


def strip_port_qualifier(val: str) -> str:
    val = _PORT_QUALIFIERS.sub("", val).strip()
    val = _PAREN_ANNOT.sub("", val).strip()
    return val


def fallback_account_name(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(
        r'(?:A/C|ACCOUNT|ACC\b|ACCT|CHARTERER)\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)["\']?(?:\s*[,\)\n\r]|$)',
        text, re.I,
    )
    if m:
        val = m.group(1).strip().rstrip(",")
        if val:
            return val
    return None


def fallback_vessel_name(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    for pat in VESSEL_NAME:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    for line in text.split("\n"):
        line = line.strip()
        if not line or ":" in line or "/" not in line:
            continue
        if line and line.isupper() and len(line) > 3 and len(line) < 80:
            skip = {"ACCOUNT", "ACCT", "DWT", "TYPE", "HIRE", "RATE", "PERIOD",
                    "VESSEL", "MV", "M/V", "CANCEL", "LAY", "DELIVERY", "REDEL",
                    "CHARTERER", "OWNER", "SUBJECT", "TEL", "FAX", "EMAIL",
                    "ATTN", "ATTENTION", "DATED", "DEAR", "PLEASE", "THANK",
                    "BEST", "REGARDS", "CC", "BCC", "COM", "COMM", "COMMISSION",
                    "BROKERAGE", "TTL", "INTENDED", "CARGO", "DEADWEIGHT",
                    "DOP", "ROP", "REDEL", "SUPRA", "ULTRA", "SMX", "UMX",
                    "SUPRA/UMX", "SUPRA/ULTRA", "SEASIA", "PACIFIC", "ATLANTIC",
                    "WORLDWIDE", "CHINA", "NOPAC", "ECSA", "WEST", "EAST",
                    "CONTINENT", "MEDITERRANEAN", "ARABIAN", "GULF"}
            first = line.split()[0] if line.split() else ""
            if first not in skip and all(w not in line.upper() for w in ["DELY", "DELIVERY", "REDEL"]):
                return line
    return None


def fallback_delivery_port(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(
        r'(?:DELY\b|DELIVER(?:Y|ED)\s+(?:AT|IN|PORT\s+OF)?)\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)["\']?(?:\s*[,\n\r]|$)',
        text, re.I,
    )
    if m:
        return m.group(1).strip()
    return None


def fallback_redelivery_port(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(
        r'(?:RE?DELIVER(?:Y|ED)\s+(?:AT|IN|PORT\s+OF)?|REDELIVERY|REDEL|RE?DEL)\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)["\']?(?:\s*[,\n\r]|$)',
        text, re.I,
    )
    if m:
        return m.group(1).strip()
    return None


def fallback_delivery_date(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'(?:LC\b|DELIVER(?:Y|ED)\s+)(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\d{1,2}\s*[-–]\s*\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+)', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'((?:FULL|MID|EARLY|LATE)\s+(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?))', text, re.I)
    if m:
        return m.group(1).strip()
    return None


def fallback_redelivery_date(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'(?:RE?DEL|REDELIVERY)\s+(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})', text, re.I)
    if m:
        return m.group(1).strip()
    return None


def fallback_charter_period(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'([\d\.\-]+\s*(?:MONTHS?|M[ONTHS]{2,}|YRS?|YEARS?|DAYS?|WKS?|WEEKS?))', text, re.I)
    if m:
        return m.group(1).strip()
    return None


def fallback_hire_rate(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'(?:HIRE|RATE)\s*[:#=]?\s*["\']?(\d[\d,\.]*)', text, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r'\$(\d[\d,\.]*)', text)
    if m:
        return m.group(1).strip()
    return None


def fallback_commission_pct(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    m = re.search(r'(\d[\d,\.]*)\s*(?:%|PCT)?\s*(?:ADDCOM|ADDOM|ADCOM|ADDCOMM|ADC)\b', text, re.I)
    if m:
        return m.group(1).strip()
    for pat in COMMISSION:
        m = pat.search(text)
        if m:
            val = m.group(1).strip()
            if val:
                return val
    m = re.search(r'(\d[\d,\.]*)\s*%', text)
    if m:
        return m.group(1).strip()
    return None


def fallback_intended_cargo(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(
        r'(?:INTEND(?:ED)?\s+CARGO|CARGO|COMMODITY|TRADE)\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)]+?)["\']?(?:\s*[,\n\r]|$)',
        text, re.I,
    )
    if m:
        return m.group(1).strip()
    m = re.search(
        r'(?:1\s+TCT|TCT)\s+WITH\s+["\']?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)]+?)["\']?(?:\s*[,\n\r]|$)',
        text, re.I,
    )
    if m:
        return m.group(1).strip()
    return None


def fallback_vessel_dwt(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    import re
    m = re.search(r'(\d[\d,\.]*)\s*K?\s*(?:DWT|DEADWEIGHT)', text, re.I)
    if m:
        return m.group(1).strip()
    m = re.search(r'(?:ABOUT|APPROX)\s+(\d[\d,\.]*)\s*(?:MT|TON)', text, re.I)
    if m:
        return m.group(1).strip()
    return None
