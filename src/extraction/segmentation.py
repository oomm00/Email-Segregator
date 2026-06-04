import re

_MV_BOUNDARY = re.compile(
    r'(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:M/V|MV)\s+',
    re.I | re.M,
)

_NUM_BOUNDARY = re.compile(
    r'(?:^|\n)\s*\d+\s*[\.\)]\s+(?:M/V|MV|VESSEL)\s+',
    re.I | re.M,
)

_HEADER_BOUNDARY = re.compile(
    r'(?:^|\n)\s*[-=*]{3,}\s*(?:\n|$)',
    re.M,
)

_SECTION_HEADERS = {
    "PACIFIC", "PACIFIC OCEAN", "INDIAN OCEAN", "ATLANTIC", "ATLANTIC OCEAN",
    "CONTINENT", "ECSA", "WEST AFRICA", "WAFR", "CONTI+MED", "CONTINENT+MED",
    "WORLDWIDE", "SEASIA", "S.E.ASIA", "SOUTHEAST ASIA", "NORTH PACIFIC",
    "NOPAC", "CHINA / NOPAC", "CHINA/NOPAC",
}

_VSL_PARTICULAR_RE = re.compile(r'^\s*VSL\s+PARTICULAR', re.I)


def segment_vessels(body_text: str) -> list[tuple[str, float]]:
    if not body_text or not body_text.strip():
        return []

    text = body_text.strip()

    # 1. try numbered list boundaries (strongest signal)
    splits = _split_by_boundary(text, _NUM_BOUNDARY, "number")

    # 2. if only one segment, try M/V boundaries
    if len(splits) <= 1:
        splits = _split_by_boundary(text, _MV_BOUNDARY, "mv")

    # 3. if still one segment, use the whole text
    if len(splits) <= 1:
        return [(text, 1.0)]

    # 4. filter: skip section headers, VSL PARTICULAR, short junk segments
    filtered = []
    for seg_text, conf in splits:
        t = seg_text.strip()
        # skip section headers
        if _is_section_header(t):
            continue
        # skip VSL PARTICULAR sections
        if _VSL_PARTICULAR_RE.match(t):
            continue
        # skip very short segments (< 15 chars that aren't real vessels)
        if len(t) < 15 and not re.search(r'(?:M/V|MV|DWT|OPEN)', t, re.I):
            continue
        filtered.append((seg_text, conf))

    return filtered if filtered else [(text, 1.0)]


def _is_section_header(text: str) -> bool:
    t = text.strip().upper()
    if t in _SECTION_HEADERS:
        return True
    # all-caps single line with ==== or ---- separator
    lines = [l.strip() for l in t.split("\n") if l.strip()]
    if len(lines) <= 2:
        main = lines[0] if lines else ""
        if main and main.isupper() and len(main) > 2 and len(main) < 40:
            if len(lines) == 1:
                return True
            second = lines[1] if len(lines) > 1 else ""
            if second and all(c in "-=*" for c in second):
                return True
    return False


def _split_by_boundary(text: str, pattern: re.Pattern, method: str) -> list[tuple[str, float]]:
    matches = list(pattern.finditer(text))
    if not matches:
        return [(text, 1.0)]

    segments = []
    prev_end = 0
    for m in matches:
        start = m.start()
        if start > prev_end:
            segment = text[prev_end:start].strip()
            if segment:
                conf = 0.9 if method == "number" else 0.85
                segments.append((segment, conf))
        prev_end = m.start()

    remainder = text[prev_end:].strip()
    if remainder:
        conf = 0.9 if method == "number" else 0.85
        segments.append((remainder, conf))

    if not segments:
        return [(text, 1.0)]

    return segments
