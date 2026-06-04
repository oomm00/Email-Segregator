"""Minimal matching engine — scores compatibility between tonnage, VC cargo, and TC fixtures."""

import re
from datetime import date, timedelta
from dataclasses import dataclass, field
from typing import Optional

from src.extraction.models import VesselExtraction
from src.extraction_cargo.models import CargoVcExtraction
from src.extraction_tc.models import TcExtraction

# ── known port -> region mapping (for approximate matching) ─
_REGION_MAP: dict[str, str] = {
    # East Coast India
    "ECI": "east coast india",
    "KANDLA": "east coast india",
    "MUNDRA": "east coast india",
    "CHENNAI": "east coast india",
    "VISAKHAPATNAM": "east coast india",
    "PARADIP": "east coast india",
    "HALDIA": "east coast india",
    "KOLKATA": "east coast india",
    "GOA": "west coast india",
    "MUMBAI": "west coast india",
    "JNPT": "west coast india",
    "HAZIRA": "west coast india",
    "MORMUGAO": "west coast india",
    "CHITTAGONG": "bangladesh",
    "SANGATTA": "indonesia",
    "KOH SI CHANG": "thailand",
    "BUSHEHR": "iran",
    "BIK": "turkey",
    "ISKENDERUN": "turkey",
    "DURBAN": "south africa",
    "BEJAIA": "algeria",
    "GABES": "tunisia",
    "CASABLANCA": "morocco",
    "MUCURIPE": "brazil",
    "SOHAR": "oman",
    "DAR ES SALAAM": "tanzania",
    "VANCOUVER": "canada west coast",
    "ECSA": "east coast south america",
    "SEASIA": "southeast asia",
    "SMX": "supramax",
    "UMX": "ultramax",
    "WW": "worldwide",
}

# ── date helpers ─────────────────────────────────────────────

_MONTHS = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
    "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5,
    "JUNE": 6, "JULY": 7, "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10,
    "NOVEMBER": 11, "DECEMBER": 12,
}


_MON_RE = '(' + '|'.join(_MONTHS) + ')'


def _parse_range(s: str | None) -> Optional[tuple[date, date]]:
    """Try to parse a date range string into (start, end). Returns None on failure."""
    if not s or not s.strip():
        return None
    s = s.strip().upper()

    year = date.today().year
    m = re.search(r'(\d{4})', s)
    if m:
        year = int(m.group(1))

    # "25 JUNE - 5 JULY" (cross-month range) — must be before single-date patterns
    dash = r'[-–—]'
    m = re.match(r'(\d{1,2})\s+' + _MON_RE + r'\s*' + dash + r'\s*(\d{1,2})\s+' + _MON_RE + r'(?:\s+(\d{4}))?', s)
    if m:
        d1, mon1, d2, mon2 = int(m.group(1)), _MONTHS[m.group(2)], int(m.group(3)), _MONTHS[m.group(4)]
        y = int(m.group(5)) if m.group(5) else year
        return date(y, mon1, d1), date(y, mon2, d2)

    # "08-12 JUNE <YEAR>" or "10-17 JUNE" (same-month range)
    m = re.match(r'(\d{1,2})\s*' + dash + r'\s*(\d{1,2})\s+' + _MON_RE + r'(?:\s+(\d{4}))?', s)
    if m:
        d1, d2 = int(m.group(1)), int(m.group(2))
        mon = _MONTHS[m.group(3)]
        y = int(m.group(4)) if m.group(4) else year
        return date(y, mon, d1), date(y, mon, d2)

    # "FULL <MONTH>"
    m = re.match(r'FULL\s+' + _MON_RE, s)
    if m:
        mon = _MONTHS[m.group(1)]
        return date(year, mon, 1), date(year, mon, 28)

    # "MID <MONTH> <YEAR>"
    m = re.match(r'MID\s+' + _MON_RE + r'(?:\s+(\d{4}))?', s)
    if m:
        mon = _MONTHS[m.group(1)]
        return date(year, mon, 10), date(year, mon, 20)

    # "1ST JUNE 2026" or "2ND JUNE 2026" — single date (last resort)
    m = re.match(r'(\d{1,2})(?:ST|ND|RD|TH)?\s+' + _MON_RE + r'(?:\s+(\d{4}))?', s)
    if m:
        d = int(m.group(1))
        mon = _MONTHS[m.group(2)]
        y = int(m.group(3)) if m.group(3) else year
        return date(y, mon, d), date(y, mon, d)

    return None


def _days_overlap(a: Optional[tuple[date, date]], b: Optional[tuple[date, date]]) -> int:
    """Return number of overlapping days between two ranges (0 if none or unparseable)."""
    if not a or not b:
        return 0
    start = max(a[0], b[0])
    end = min(a[1], b[1])
    return max(0, (end - start).days + 1)


def _s(value) -> str:
    """Safely get the string value from an ExtractedField or None."""
    return value.value.upper().strip() if value and value.value else ""


def _num(value) -> Optional[float]:
    """Parse a numeric string from an ExtractedField, handling commas."""
    raw = _s(value)
    if not raw:
        return None
    raw = raw.replace(",", "")
    try:
        return float(raw)
    except ValueError:
        return None


# ── port scoring ────────────────────────────────────────────

def _port_score(vessel_port: str, target_port: str, max_score: float = 40.0) -> float:
    vp = vessel_port.upper().strip()
    tp = target_port.upper().strip()
    if not vp or not tp:
        return 0.0

    # exact match
    if vp == tp:
        return max_score

    # one contains the other
    if vp in tp or tp in vp:
        return max_score * 0.8

    # word overlap
    v_words = set(vp.split())
    t_words = set(tp.split())
    common = v_words & t_words
    if common:
        return max_score * 0.4

    # region match
    v_reg = _REGION_MAP.get(vp) or _REGION_MAP.get(vp.split()[0])
    t_reg = _REGION_MAP.get(tp) or _REGION_MAP.get(tp.split()[0])
    if v_reg and t_reg and v_reg == t_reg:
        return max_score * 0.6

    return 0.0


# ── size scoring ────────────────────────────────────────────

def _size_score(vessel_dwt_val: Optional[float],
                qty_min: Optional[float],
                qty_max: Optional[float],
                max_score: float = 20.0) -> float:
    if vessel_dwt_val is None:
        return 0.0
    if qty_min is None:
        return 0.0
    q_high = qty_max or qty_min * 1.3
    # vessel DWT should be >= min quantity
    if vessel_dwt_val < qty_min * 0.7:
        return 0.0
    # perfect when vessel can carry the full cargo
    if vessel_dwt_val >= qty_min and (qty_max is None or vessel_dwt_val <= qty_max * 1.2):
        return max_score
    if vessel_dwt_val >= qty_min * 0.7:
        return max_score * 0.5
    return 0.0


# ── cargo compat ────────────────────────────────────────────

_BULK_KEYWORDS = {"BULK", "GRAIN", "ORE", "COAL", "AGRI"}
_BREAKBULK_KEYWORDS = {"STEEL", "STEELS", "GEN", "GENERAL", "BREAKBULK", "PROJECT"}


def _cargo_score(vessel_type: str, cargo_name: str, max_score: float = 10.0) -> float:
    vt = vessel_type.upper()
    cn = cargo_name.upper()
    if not vt or not cn:
        return 5.0  # neutral — no info to penalise

    is_bulk_vessel = any(k in vt for k in _BULK_KEYWORDS)
    is_breakbulk_cargo = any(k in cn for k in _BREAKBULK_KEYWORDS)

    if is_bulk_vessel and not is_breakbulk_cargo:
        return max_score
    if not is_bulk_vessel and is_breakbulk_cargo:
        return max_score
    return max_score * 0.5


# ── match result ────────────────────────────────────────────

@dataclass
class Match:
    score: float
    label: str
    source_type: str
    source_ref: str
    target_type: str
    target_ref: str
    details: dict = field(default_factory=dict)


# ── engine ──────────────────────────────────────────────────

class MatchingEngine:
    def match_all(
        self,
        vessels: list[VesselExtraction],
        cargoes: list[CargoVcExtraction],
        fixtures: list[TcExtraction],
    ) -> list[Match]:
        matches: list[Match] = []

        # 1. Vessel → VC Cargo (open vessel for a cargo)
        for v in vessels:
            v_name = _s(v.vessel_name)
            for c in cargoes:
                score, details = self._score_vessel_cargo(v, c)
                if score > 0:
                    matches.append(Match(
                        score=score,
                        label=f"{v_name} -> {_s(c.cargo_name)}",
                        source_type="tonnage",
                        source_ref=v_name or _s(v.account_name),
                        target_type="vc_cargo",
                        target_ref=_s(c.cargo_name) or _s(c.loading_port),
                        details=details,
                    ))

        # 2. Vessel → TC (vessel positioned for TC delivery)
        for v in vessels:
            v_name = _s(v.vessel_name)
            for t in fixtures:
                score, details = self._score_vessel_tc(v, t)
                if score > 0:
                    matches.append(Match(
                        score=score,
                        label=f"{v_name} -> {_s(t.intended_cargo) or _s(t.delivery_port)} TC",
                        source_type="tonnage",
                        source_ref=v_name or _s(v.account_name),
                        target_type="tc_fixture",
                        target_ref=_s(t.account_name) or _s(t.intended_cargo),
                        details=details,
                    ))

        # 3. TC → VC Cargo (TC redelivery aligns with VC loading)
        for t in fixtures:
            t_acct = _s(t.account_name)
            for c in cargoes:
                score, details = self._score_tc_cargo(t, c)
                if score > 0:
                    matches.append(Match(
                        score=score,
                        label=f"{t_acct} TC -> {_s(c.cargo_name)}",
                        source_type="tc_fixture",
                        source_ref=t_acct or _s(t.intended_cargo),
                        target_type="vc_cargo",
                        target_ref=_s(c.cargo_name) or _s(c.loading_port),
                        details=details,
                    ))

        matches.sort(key=lambda m: m.score, reverse=True)
        return matches

    def _score_vessel_cargo(self, v: VesselExtraction, c: CargoVcExtraction) -> tuple[float, dict]:
        port = _port_score(_s(v.open_port), _s(c.loading_port))
        v_date = _parse_range(_s(v.open_date))
        c_date = _parse_range(_s(c.laycan))
        overlap_days = _days_overlap(v_date, c_date)
        date_s = min(30.0, overlap_days * 10.0)

        v_dwt = _num(v.vessel_size_dwt)
        q_min = _num(c.quantity_min_mt)
        q_max = _num(c.quantity_max_mt) or (q_min * 1.3 if q_min else None)
        size = _size_score(v_dwt, q_min, q_max)

        cargo_s = _cargo_score(_s(v.vessel_type), _s(c.cargo_name))

        total = port + date_s + size + cargo_s
        return total, {
            "port_score": round(port, 1),
            "date_score": round(date_s, 1),
            "size_score": round(size, 1),
            "cargo_score": round(cargo_s, 1),
            "overlap_days": overlap_days,
        }

    def _score_vessel_tc(self, v: VesselExtraction, t: TcExtraction) -> tuple[float, dict]:
        # vessel open port vs TC delivery port
        port = _port_score(_s(v.open_port), _s(t.delivery_port))
        if not port:
            port = _port_score(_s(v.open_port), _s(t.redelivery_port)) * 0.7

        v_date = _parse_range(_s(v.open_date))
        t_date = _parse_range(_s(t.delivery_date))
        overlap_days = _days_overlap(v_date, t_date)
        date_s = min(30.0, overlap_days * 10.0)

        v_dwt = _num(v.vessel_size_dwt)
        t_dwt = _num(t.vessel_dwt)
        size = 10.0
        if v_dwt and t_dwt:
            ratio = v_dwt / t_dwt if t_dwt else 0
            if 0.8 <= ratio <= 1.25:
                size = 20.0
            elif 0.6 <= ratio <= 1.5:
                size = 10.0
            else:
                size = 0.0

        cargo_s = _cargo_score(_s(v.vessel_type), _s(t.intended_cargo))

        total = port + date_s + size + cargo_s
        return total, {
            "port_score": round(port, 1),
            "date_score": round(date_s, 1),
            "size_score": round(size, 1),
            "cargo_score": round(cargo_s, 1),
            "overlap_days": overlap_days,
        }

    def _score_tc_cargo(self, t: TcExtraction, c: CargoVcExtraction) -> tuple[float, dict]:
        # TC redelivery port vs VC loading port — back-to-back opportunity
        port = _port_score(_s(t.redelivery_port), _s(c.loading_port))

        v_dwt = _num(t.vessel_dwt)
        q_min = _num(c.quantity_min_mt)
        q_max = _num(c.quantity_max_mt) or (q_min * 1.3 if q_min else None)
        size = _size_score(v_dwt, q_min, q_max) * 0.5

        cargo_s = _cargo_score(_s(t.intended_cargo), _s(c.cargo_name))

        # cargo name mentions the intended cargo — bonus for alignment
        cargo_bonus = 5.0 if cargo_s > 0 else 0.0

        total = port + size + cargo_s + cargo_bonus
        return total, {
            "port_score": round(port, 1),
            "date_score": 0.0,
            "size_score": round(size, 1),
            "cargo_score": round(cargo_s + cargo_bonus, 1),
            "overlap_days": 0,
        }
