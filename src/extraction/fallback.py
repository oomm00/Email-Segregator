import re

from src.extraction.regex_patterns import VESSEL_NAME, VESSEL_TYPE, VESSEL_SIZE_DWT
from src.extraction.confidence import make_field, score_vessel_name, score_vessel_type, score_vessel_size_dwt

_LINE_VESSEL_PREFIX = re.compile(r'^\s*(?:[-*]\s*)?["\']?([A-Z][A-Za-z0-9\s\-\.\'\"\(\)\/]+?)["\']?\s*$', re.M)


def fallback_vessel_name(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    for pat in VESSEL_NAME:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    # take the first all-caps line that looks like a vessel name
    for line in text.split("\n"):
        line = line.strip()
        if line and line.isupper() and len(line) > 3 and len(line) < 80:
            skip = {"ACCOUNT", "ACCT", "DWT", "TYPE", "OPEN", "LOAD", "PORT", "VESSEL",
                    "MV", "M/V", "CANCEL", "LAY", "LAYDAYS", "DELIVERY", "CHARTERER",
                    "OWNER", "REMARKS", "NOTES", "SUBJECT", "TEL", "FAX", "EMAIL",
                    "ATTN", "ATTENTION", "DATED", "DEAR", "PLEASE", "THANK", "BEST",
                    "REGARDS", "CC", "BCC", "OUR", "DIRECT", "OWS", "AS", "FOLLOWS",
                    "PRIME", "MARITIME", "INC", "PIRAEUS", "HAMBURG", "LONDON",
                    "SINGAPORE", "TOKYO", "HONG", "KONG", "SHANGHAI", "DUBAI",
                    "ABT", "ABOUT", "GRT", "NRT", "LOA", "BEAM", "DRAFT", "FLAG",
                    "CLASS", "BUILT", "YARD", "IMO", "CALL", "SIGN", "GPS", "SSW",
                    "GRAIN", "BALE", "HOPPER", "HATCH", "CRANES", "GEARED", "GEARLESS",
                    "SPEED", "CONS", "CONSUMPTION", "BALLAST", "LADEN", "PORT", "IDLE",
                    "ECSA", "WEST", "AFRICA", "CONTINENT", "MEDITERRANEAN", "PACIFIC",
                    "INDIAN", "ATLANTIC", "OCEAN", "WORLDWIDE", "SEASIA", "NOPAC",
                    "CHINA", "VIETNAM", "INDONESIA", "PHILIPPINES", "MALAYSIA",
                    "THAILAND", "B.DESH", "PAKISTAN", "INDIA", "SRI", "LANKA",
                    "BRAZIL", "ARGENTINA", "URUGUAY", "VSL", "PARTICULAR",
                    "HO/HA", "HO", "HA", "TPC", "MT", "MTS", "KTS", "KNOTS",
                    "LSFO", "MGO", "MDO", "HFO", "IFO", "SCRUBBER", "FITTED",
                    "SSW", "SCANTLING", "SDBC", "SDSTBC", "BLT", "PRC", "CCS",
                    "ABS", "NK", "KR", "DNV", "GL", "LR", "BV", "RINA",
                    "IMO", "NO", "CALL", "SIGN", "BPNY", "BP", "YARD"}
            first = line.split()[0] if line.split() else ""
            if first not in skip and not any(ws in line.lower() for ws in ["@", "http", "www."]):
                return line
    return None


def fallback_account_name(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    m = re.search(r'(?:ACCOUNT|ACCT|CHARTERER)\s*[:#=]?\s*["\']?([A-Za-z][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)["\']?(?:\s*[,\)\n\r]|$)', text, re.I)
    if m:
        val = m.group(1).strip().rstrip(",")
        if val:
            return val
    return None


def fallback_open_port(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    m = re.search(r'(?:AT|IN)\s+PORT\s+OF\s+["\']?([A-Za-z][A-Za-z\s\-]+?)["\']?(?:\s*[,\n\r]|$)', text, re.I)
    if m:
        return m.group(1).strip()
    # "OPEN <port>" without label (skip non-port words)
    m = re.search(r'OPEN\s+["\']?(?!HATC\b|BOX\b|HATCH\b)([A-Z][A-Za-z\s\-\.\'\"\(\)]+?)["\']?(?:\s*[,\n\r]|$)', text, re.I)
    if m:
        return m.group(1).strip()
    # port after dash in MV line: "MV TRUE FRIEND ... - BEJAIA, 1ST JUNE"
    m = re.search(r'(?:^|\n)\s*(?:M/V|MV)\s+\S+.*?\s+[-–]\s+["\']?([A-Z][A-Za-z\s\-\.]+?)["\']?(?=\s*,|\s+\d)', text, re.I | re.M)
    if m:
        return m.group(1).strip()
    return None


def fallback_open_date(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    m = re.search(r'(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})', text)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})', text)
    if m:
        return m.group(1).strip()
    return None


def fallback_vessel_type(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    for pat in VESSEL_TYPE:
        m = pat.search(text)
        if m:
            return m.group(1).strip()
    return None


def fallback_vessel_size_dwt(text: str, existing: str | None) -> str | None:
    if existing:
        return existing
    m = re.search(r'(\d[\d,]*)\s*(?:DWT|MT|DEADWEIGHT)', text, re.I)
    if m:
        return m.group(1).strip()
    return None
