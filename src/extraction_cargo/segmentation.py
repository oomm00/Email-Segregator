import re

_CARGO_BOUNDARY = re.compile(
    r'(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:CARGO|COMMODITY|PRODUCT)\s+(?!TYPE|QUANTITY|QTY)(?:DESCRIPTION|NAME)?\s*[:#]?\s*(?=[A-Z])',
    re.I | re.M,
)

_NUM_BOUNDARY = re.compile(
    r'(?:^|\n)\s*\d+\s*[\.\)]\s+(?:CARGO|COMMODITY|PRODUCT|ACCOUNT|CHARTERER)\s*[:#]?\s*',
    re.I | re.M,
)

_HEADER_BOUNDARY = re.compile(
    r'(?:^|\n)\s*[-=*]{3,}\s*(?:\n|$)',
    re.M,
)


def segment_cargoes(body_text: str) -> list[tuple[str, float]]:
    if not body_text or not body_text.strip():
        return []

    text = body_text.strip()

    splits = _split_by_boundary(text, _NUM_BOUNDARY, "number")
    if len(splits) <= 1:
        splits = _split_by_boundary(text, _CARGO_BOUNDARY, "cargo")
    if len(splits) <= 1:
        return [(text, 1.0)]

    return splits


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
