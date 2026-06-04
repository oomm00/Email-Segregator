import logging
import re

logger = logging.getLogger(__name__)


def segment_tc_vessels(text: str) -> list[str]:
    segments = []
    seen = set()

    # 1) Numbered-list boundaries
    numbered = re.split(r'(?:^|\n)\s*\d+[\.\)]\s+', text.strip())
    candidates = [s.strip() for s in numbered if s.strip()]

    if len(candidates) > 1:
        for s in candidates:
            if re.search(r'(?:M/V|MV|VESSEL|ACCOUNT|CHARTERER|OWNER|A/C|ACC\b)', s, re.I):
                dedup_key = s[:80].lower()
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    segments.append(s)
        if segments:
            return segments

    # 2) ACCOUNT / CHARTERER / OWNER / A/C boundaries (vessel-level only)
    boundaries = list(
        re.finditer(
            r'(?:^|\n)(?=(?:A/C(?=\s+[A-Z])|(?:ACCOUNT|ACC\b|CHARTERER|OWNERS?)\s*[:#=]))',
            text, re.I | re.M
        )
    )
    if len(boundaries) > 1:
        for i, m in enumerate(boundaries):
            start = m.start()
            end = boundaries[i + 1].start() if i + 1 < len(boundaries) else len(text)
            seg = text[start:end].strip()
            if seg:
                dedup_key = seg[:80].lower()
                if dedup_key not in seen:
                    seen.add(dedup_key)
                    segments.append(seg)
        if segments:
            return segments

    # 3) Fallback: whole text
    segments = [text.strip()] if text.strip() else []
    return segments
