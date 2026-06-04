import re

import pytest

from src.extraction_tc.pipeline import run_tc_pipeline
from src.extraction_tc.models import TcExtraction, ExtractedField
from src.extraction_tc.segmentation import segment_tc_vessels
from src.extraction_tc.regex_patterns import (
    ACCOUNT_NAME, VESSEL_NAME, DELIVERY_PORT, DELIVERY_DATE,
    REDELIVERY_PORT, REDELIVERY_DATE, CHARTER_PERIOD, HIRE_RATE,
    COMMISSION, INTENDED_CARGO, VESSEL_DWT,
)
from src.extraction_tc.confidence import (
    make_field, score_account_name,
)


# ─── Fixtures ─────────────────────────────────────────────────


SINGLE_FULL = """ACCOUNT: Delta Shipping Co.
VESSEL: M/V Ocean Star
DELIVERY: Port Said
LAY/CAN: 05-10 Jan 2026
REDELIVERY: Gibraltar
REDEL: 15-20 Apr 2026
PERIOD: 6 months
HIRE: $12,500 per day
COM: 1.25%
INTENDED CARGO: Grains / Agri-Bulk
DWT: 82,000"""

MULTI_TC = """1. ACCOUNT: Apex Maritime
   VESSEL: M/V Nordic Voyager
   DELIVERY: Skaw
   LAYCAN: 10-15 Feb 2026
   REDEL: Singapore range
   REDEL DATE: 10-15 Aug 2026
   PERIOD: 6 months
   HIRE: $13,200
   COMM: 1.25%
   CARGO: Coal / Coke
   DWT: 78,500

2. ACCOUNT: Gulf Bulk Carriers
   VESSEL: M/V Atlantic Breeze
   DELIVERY: Port Hedland
   LAY/CAN: 01-05 Mar 2026
   REDELIVERY: Rotterdam / ARA
   REDEL DATE: 01-05 Sep 2026
   PERIOD: 6 months
   HIRE: $14,000
   COM: 1.00%
   CARGO: Iron Ore
   DWT: 95,000"""

PROSE_TC = """We are pleased to present an interesting Time Charter opportunity.
ACCOUNT: Pacific Line Ltd
Subject vessel M/V Southern Cross open for delivery at Dalian.
Laycan 20-25 March 2026. Redelivery options West Africa / North Brazil
range. Redel date estimated Jun/Jul 2026. Charter period about 6 months.
Hire rate USD 11,800 per day. Commission 2.5% total. Intended cargo
bauxite / alumina. DWT approx 65,000."""

COMPACT_TC = """ACCT: Consolidated Shippers / MV Cape Adventure / DELIVERY: Jorf Lasfar /
LAY: 15-20 Jan 2026 / REDEL: US Gulf / REDEL DATE: 15-20 Jul 2026 /
PERIOD: 6 / HIRE: 12,000 / COM: 1.25 / CARGO: Phosphate / DWT: 72K"""

SHORT_TC = """ACCOUNT: Atlantic Carriers Inc
VESSEL: MV Golden Eagle
DELIVERY PORT: Las Palmas
LAY: 10 Jan 2026
REDEL: Cape Town
REDEL DATE: 10 Jul 2026
PERIOD: 6 mos
HIRE: 13000
COM: 1%
DWT: 55000"""

OWNER_FORMAT = """OWNER: Northern Star Shipmanagement
M/V Diamond Sea
Delivery at Rotterdam 05-10 Jun 2026
Laycan 05-10 Jun 2026. Redelivery Singapore.
Redel 05-10 Dec 2026. Period 12 months.
Hire rate $9,500. Brokerage 2.5%.
Intended cargo forest products / lumber.
Deadweight 58,000 MT."""

CHARTERER_FORMAT = """CHARTERER: Global Commodities Ltd
M/V Star Navigator for TC
Delivery Port: Tubarao. Laycan 20-25 Jul 2026.
Redelivery Port: Richards Bay.
Redel Date 20-25 Jan 2027. Period 6 months.
Hire $16,000 per day. Commission 1.5%.
Cargo: Iron Ore / Pellets.
Vessel DWT 105,000."""

EMPTY = ""
NO_VESSEL = """We confirm the following terms for the above."""


# ─── Segmentation Tests ────────────────────────────────────────


class TestSegmentation:
    def test_single_full(self):
        segs = segment_tc_vessels(SINGLE_FULL)
        assert len(segs) == 1
        assert "Delta Shipping" in segs[0]

    def test_multi(self):
        segs = segment_tc_vessels(MULTI_TC)
        assert len(segs) == 2
        assert "Apex Maritime" in segs[0]
        assert "Gulf Bulk" in segs[1]

    def test_prose(self):
        segs = segment_tc_vessels(PROSE_TC)
        assert len(segs) == 1

    def test_empty(self):
        segs = segment_tc_vessels(EMPTY)
        assert segs == []

    def test_no_vessel(self):
        segs = segment_tc_vessels(NO_VESSEL)
        assert len(segs) == 1

    def test_compact(self):
        segs = segment_tc_vessels(COMPACT_TC)
        assert len(segs) == 1


# ─── Regex Pattern Tests ────────────────────────────────────────


class TestRegexPatterns:
    def test_account_name_labeled(self):
        m = ACCOUNT_NAME[0].search("ACCOUNT: Delta Shipping Co.")
        assert m and "Delta Shipping Co." in m.group(1)

    def test_account_name_charterer(self):
        m = ACCOUNT_NAME[0].search("CHARTERER: Global Commodities Ltd")
        assert m and "Global Commodities Ltd" in m.group(1)

    def test_account_name_owner(self):
        m = ACCOUNT_NAME[0].search("OWNER: Northern Star Shipmanagement")
        assert m and "Northern Star Shipmanagement" in m.group(1)

    def test_vessel_name_mv(self):
        m = VESSEL_NAME[0].search("M/V Ocean Star")
        assert m and "Ocean Star" in m.group(1)

    def test_vessel_name_mv_compact(self):
        m = VESSEL_NAME[0].search("MV Cape Adventure")
        assert m and "Cape Adventure" in m.group(1)

    def test_vessel_name_labeled(self):
        m = VESSEL_NAME[1].search("VESSEL: M/V Nordic Voyager")
        assert m and "M/V Nordic Voyager" in m.group(1)

    def test_delivery_port_labeled(self):
        m = DELIVERY_PORT[1].search("DELIVERY: Port Said")
        assert m and "Port Said" in m.group(1)

    def test_delivery_port_at(self):
        m = DELIVERY_PORT[2].search("Delivery at Rotterdam")
        assert m and "Rotterdam" in m.group(1)

    def test_delivery_date_laycan(self):
        m = DELIVERY_DATE[1].search("LAY/CAN: 05-10 Jan 2026")
        assert m and "05-10 Jan 2026" in m.group(1)

    def test_delivery_date_laydown(self):
        m = DELIVERY_DATE[1].search("LAYDATE: 10-15 Feb 2026")
        assert m and "10-15 Feb 2026" in m.group(1)

    def test_delivery_date_pwwd(self):
        m = DELIVERY_DATE[1].search("PWWD: 15-20 Jan 2026")
        assert m and "15-20 Jan 2026" in m.group(1)

    def test_delivery_date_basis(self):
        m = DELIVERY_DATE[4].search("basis delivery 20-25 Jul 2026")
        assert m and "20-25 Jul 2026" in m.group(1)

    def test_redelivery_port_labeled(self):
        m = REDELIVERY_PORT[1].search("REDELIVERY: Gibraltar")
        assert m and "Gibraltar" in m.group(1)

    def test_redelivery_port_redel(self):
        m = REDELIVERY_PORT[2].search("REDEL: Singapore range")
        assert m and "Singapore range" in m.group(1)

    def test_redelivery_port_rop(self):
        m = REDELIVERY_PORT[0].search("ROP: US Gulf")
        assert m and "US Gulf" in m.group(1)

    def test_redelivery_date_labeled(self):
        m = REDELIVERY_DATE[1].search("REDELIVERY DATE: 15-20 Apr 2026")
        assert m and "15-20 Apr 2026" in m.group(1)

    def test_redelivery_date_redel(self):
        m = REDELIVERY_DATE[1].search("REDEL DATE: 15-20 Apr 2026")
        assert m and "15-20 Apr 2026" in m.group(1)

    def test_charter_period_months(self):
        m = CHARTER_PERIOD[0].search("PERIOD: 6 months")
        assert m and "6 months" in m.group(1)

    def test_charter_period_year(self):
        m = CHARTER_PERIOD[0].search("Period 12 months")
        assert m and "12 months" in m.group(1)

    def test_charter_period_about(self):
        m = CHARTER_PERIOD[3].search("about 6 months")
        assert m and "6 months" in m.group(1)

    def test_hire_rate_labeled(self):
        m = HIRE_RATE[0].search("HIRE: $12,500 per day")
        assert m and "12,500" in m.group(1)

    def test_hire_rate_dollar(self):
        m = HIRE_RATE[1].search("$13,200 per day")
        assert m and "13,200" in m.group(1)

    def test_commission_labeled(self):
        m = COMMISSION[0].search("COM: 1.25%")
        assert m and "1.25" in m.group(1)

    def test_commission_ttl(self):
        m = COMMISSION[0].search("TTL: 2.5%")
        assert m and "2.5" in m.group(1)

    def test_commission_brokerage(self):
        m = COMMISSION[0].search("Brokerage 2.5%")
        assert m and "2.5" in m.group(1)

    def test_intended_cargo_labeled(self):
        m = INTENDED_CARGO[0].search("INTENDED CARGO: Grains / Agri-Bulk")
        assert m and "Grains / Agri-Bulk" in m.group(1)

    def test_intended_cargo_commodity(self):
        m = INTENDED_CARGO[1].search("COMMODITY: Iron Ore")
        assert m and "Iron Ore" in m.group(1)

    def test_vessel_dwt_labeled(self):
        m = VESSEL_DWT[0].search("DWT: 82,000")
        assert m and "82,000" in m.group(1)

    def test_vessel_dwt_deadweight(self):
        m = VESSEL_DWT[2].search("Deadweight 58,000 MT")
        assert m and "58,000" in m.group(1)

    def test_vessel_name_not_capturing_account(self):
        text = "ACCOUNT: Delta Shipping Co."
        m = VESSEL_NAME[0].search(text)
        assert not m


# ─── Confidence Tests ─────────────────────────────────────────


class TestConfidence:
    def test_regex_labeled(self):
        f = make_field("Delta Shipping", "regex_labeled", score_account_name)
        assert f.confidence == 0.9
        assert f.method == "regex_labeled"

    def test_spacy(self):
        f = make_field("Delta Shipping", "spacy", score_account_name)
        assert f.confidence == 0.7
        assert f.method == "spacy"

    def test_fallback(self):
        f = make_field("Delta Shipping", "fallback", score_account_name)
        assert f.confidence == 0.35
        assert f.method == "fallback"

    def test_empty_value(self):
        f = make_field("", "regex_labeled", score_account_name)
        assert f.confidence == 0.0
        assert f.value == ""


# ─── Pipeline Tests — Single Vessel ────────────────────────────


class TestPipelineSingle:
    def test_single_full(self):
        results = run_tc_pipeline("test", SINGLE_FULL)
        assert len(results) == 1
        tc = results[0]
        assert tc.account_name.value == "Delta Shipping Co."
        assert tc.vessel_name.value == "Ocean Star"
        assert tc.delivery_port.value == "Port Said"
        assert tc.delivery_date.value is not None
        assert tc.redelivery_port.value == "Gibraltar"
        assert tc.redelivery_date.value is not None
        assert tc.charter_period.value is not None
        assert tc.hire_rate.value is not None
        assert tc.commission_pct.value is not None
        assert tc.intended_cargo.value is not None
        assert tc.vessel_dwt.value is not None
        assert tc.overall_confidence > 0.5

    def test_owner_format(self):
        results = run_tc_pipeline("test", OWNER_FORMAT)
        assert len(results) == 1
        tc = results[0]
        assert tc.account_name.value == "Northern Star Shipmanagement"
        assert tc.vessel_name.value is not None
        assert tc.delivery_port.value is not None
        assert tc.delivery_date.value is not None

    def test_charterer_format(self):
        results = run_tc_pipeline("test", CHARTERER_FORMAT)
        assert len(results) == 1
        tc = results[0]
        assert tc.account_name.value is not None
        assert tc.vessel_name.value is not None
        assert tc.delivery_port.value is not None
        assert tc.delivery_date.value is not None
        assert tc.redelivery_port.value is not None
        assert tc.redelivery_date.value is not None

    def test_short_tc(self):
        results = run_tc_pipeline("test", SHORT_TC)
        assert len(results) == 1
        tc = results[0]
        assert tc.account_name.value is not None
        assert tc.vessel_name.value is not None
        assert tc.delivery_port.value is not None
        assert tc.delivery_date.value is not None
        assert tc.redelivery_port.value is not None
        assert tc.redelivery_date.value is not None
        assert tc.charter_period.value is not None


# ─── Pipeline Tests — Multi-Vessel ─────────────────────────────


class TestPipelineMulti:
    def test_multi_tc(self):
        results = run_tc_pipeline("test", MULTI_TC)
        assert len(results) == 2
        r0, r1 = results
        assert r0.account_name.value == "Apex Maritime"
        assert r1.account_name.value == "Gulf Bulk Carriers"
        assert r0.vessel_dwt.value is not None
        assert r1.vessel_dwt.value is not None
        assert r0.segment_index == 0
        assert r1.segment_index == 1


# ─── Pipeline Tests — Prose Style ──────────────────────────────


class TestPipelineProse:
    def test_prose_tc(self):
        results = run_tc_pipeline("test", PROSE_TC)
        assert len(results) == 1
        tc = results[0]
        assert tc.account_name.value is not None
        assert tc.vessel_name.value is not None
        assert tc.delivery_port.value is not None
        assert tc.delivery_date.value is not None


# ─── Pipeline Tests — Compact Format ───────────────────────────


class TestPipelineCompact:
    def test_compact_tc(self):
        results = run_tc_pipeline("test", COMPACT_TC)
        assert len(results) == 1
        tc = results[0]
        assert tc.account_name.value is not None
        assert tc.vessel_name.value is not None
        assert tc.delivery_port.value is not None


# ─── Pipeline Tests — Edge Cases ───────────────────────────────


class TestPipelineEdgeCases:
    def test_empty_body(self):
        results = run_tc_pipeline("test", "")
        assert results == []

    def test_no_vessel_segment_filtered(self):
        results = run_tc_pipeline("test", NO_VESSEL)
        assert len(results) == 0

    def test_record_dict_contains_fields(self):
        results = run_tc_pipeline("test", SINGLE_FULL)
        assert len(results) == 1
        d = results[0].to_record_dict()
        assert "account_name" in d
        assert "vessel_name" in d
        assert "delivery_port" in d
        assert "delivery_date" in d
        assert "_segment_index" in d

    def test_record_dict_values(self):
        results = run_tc_pipeline("test", SINGLE_FULL)
        d = results[0].to_record_dict()
        assert d["account_name"]["value"] == "Delta Shipping Co."
        assert d["account_name"]["confidence"] > 0

    def test_overall_confidence_no_fields(self):
        tc = TcExtraction()
        assert tc.overall_confidence == 0.0

    def test_overall_confidence_some_fields(self):
        tc = TcExtraction(
            account_name=ExtractedField(value="Test", confidence=0.9, method="regex_labeled"),
            vessel_name=ExtractedField(value="Test", confidence=0.95, method="regex_labeled"),
        )
        assert tc.overall_confidence > 0.0


# ─── Validation Tests ──────────────────────────────────────────


class TestValidation:
    def test_validation_clean(self):
        from src.extraction_tc.validation import validate_tc_extraction
        from src.extraction_tc.models import TcExtraction, ExtractedField
        tc = TcExtraction(
            account_name=ExtractedField(value="Test", confidence=0.9, method="regex_labeled"),
            vessel_name=ExtractedField(value="Test", confidence=0.95, method="regex_labeled"),
            delivery_date=ExtractedField(value="05-10 Jan 2026", confidence=0.9, method="regex_labeled"),
            redelivery_date=ExtractedField(value="15-20 Apr 2026", confidence=0.9, method="regex_labeled"),
            commission_pct=ExtractedField(value="1.25", confidence=0.9, method="regex_labeled"),
            delivery_port=ExtractedField(value="Port Said", confidence=0.9, method="regex_labeled"),
            redelivery_port=ExtractedField(value="Gibraltar", confidence=0.9, method="regex_labeled"),
        )
        w = validate_tc_extraction(tc)
        assert len(w) == 0

    def test_validation_commission_range(self):
        from src.extraction_tc.validation import validate_tc_extraction
        from src.extraction_tc.models import TcExtraction, ExtractedField
        tc = TcExtraction(
            commission_pct=ExtractedField(value="150", confidence=0.9, method="regex_labeled"),
        )
        w = validate_tc_extraction(tc)
        assert any("commission" in x.lower() for x in w)

    def test_validation_same_ports(self):
        from src.extraction_tc.validation import validate_tc_extraction
        from src.extraction_tc.models import TcExtraction, ExtractedField
        tc = TcExtraction(
            delivery_port=ExtractedField(value="Rotterdam", confidence=0.9, method="regex_labeled"),
            redelivery_port=ExtractedField(value="Rotterdam", confidence=0.9, method="regex_labeled"),
        )
        w = validate_tc_extraction(tc)
        assert any("same" in x.lower() for x in w)

    def test_validation_bad_hire_rate(self):
        from src.extraction_tc.validation import validate_tc_extraction
        from src.extraction_tc.models import TcExtraction, ExtractedField
        tc = TcExtraction(
            hire_rate=ExtractedField(value="TBD", confidence=0.3, method="fallback"),
        )
        w = validate_tc_extraction(tc)
        assert any("hire_rate" in x.lower() for x in w)


# ─── Real-World TC Email Regression Tests ─────────────────────


TC_1 = """CHINA / NOPAC
ACC DAI AN OCEAN SHIPPING COMPANY LIMITED
DELIVERY TM VANCOUVER
LC 10-17 JUNE
SMX-UMX, PREF UMX
1 TCT WITH GRAINS
REDELIVERY CHITTAGONG
3.75 ADDCOM PUS"""

TC_2 = """SEASIA
ACC DAI AN OCEAN SHIPPING COMPANY LIMITED
SMX-UMX MAX 20 YRS.
DELY TO MAKE SANGATTA (NEAR TO TJ BARA), E KALI OF INDONESIA.
29-2ND JUN
1 TCT WITH CLINKER TO BDESH.
DURATION ABT 30 DAYS WOG.
3.75PCT ADDOM PUS"""

TC_3 = """WORLDWIDE
ACC DAI AN OCEAN SHIPPING COMPANY LIMITED
SUPRA/ULTRA DELY WW
FULL MAY
1-3 YEARS TRY SHORT PERIOD
FLAT OR INDEX BOTH WORKABLE
3.75 ADDCOM PUS"""

TC_4 = """A/C SeaSchiffe
1 TCT with Steels/Gens/lawfuls
22k dwt upto HMAX
Delivery: ECI
Laycan: 15-18 July
Redel: Med via GOA transit
Duration: abt 35-40 days wog
3.75% Adc"""

TC_5 = """A/C SeaSchiffe
1 TCT with Steels/Gens/lawfuls
33k dwt upto HMAX
Delivery: ECI
Laycan: 21-23 July
Redel: ARAG via COGH transit
Duration: abt 50-55 days wog
3.75% Adc"""


def assert_field(tc, name, expected=None):
    val = getattr(tc, name)
    if expected is None:
        return val is not None and val.value
    assert val is not None and val.value is not None, f"{name} should have value, got None"
    assert expected.upper() in val.value.upper(), f"{name}: expected '{expected}' in '{val.value}'"


class TestPipelineTCRealWorld:
    def test_tc1_account_name(self):
        results = run_tc_pipeline("test", TC_1)
        assert len(results) >= 1
        assert_field(results[0], "account_name", "DAI AN OCEAN")

    def test_tc1_delivery_port(self):
        results = run_tc_pipeline("test", TC_1)
        assert len(results) >= 1
        assert_field(results[0], "delivery_port", "VANCOUVER")

    def test_tc1_delivery_date(self):
        results = run_tc_pipeline("test", TC_1)
        assert len(results) >= 1
        assert_field(results[0], "delivery_date", "10-17 JUNE")

    def test_tc1_redelivery_port(self):
        results = run_tc_pipeline("test", TC_1)
        assert len(results) >= 1
        assert_field(results[0], "redelivery_port", "CHITTAGONG")

    def test_tc1_commission(self):
        results = run_tc_pipeline("test", TC_1)
        assert len(results) >= 1
        assert_field(results[0], "commission_pct", "3.75")

    def test_tc1_intended_cargo(self):
        results = run_tc_pipeline("test", TC_1)
        assert len(results) >= 1
        assert_field(results[0], "intended_cargo", "GRAINS")

    def test_tc2_account_name(self):
        results = run_tc_pipeline("test", TC_2)
        assert len(results) >= 1
        assert_field(results[0], "account_name", "DAI AN OCEAN")

    def test_tc2_delivery_date_ordinal(self):
        results = run_tc_pipeline("test", TC_2)
        assert len(results) >= 1
        assert_field(results[0], "delivery_date", "29")

    def test_tc2_intended_cargo(self):
        results = run_tc_pipeline("test", TC_2)
        assert len(results) >= 1
        assert_field(results[0], "intended_cargo", "CLINKER")

    def test_tc2_charter_period(self):
        results = run_tc_pipeline("test", TC_2)
        assert len(results) >= 1
        assert_field(results[0], "charter_period", "30 DAYS")

    def test_tc2_commission(self):
        results = run_tc_pipeline("test", TC_2)
        assert len(results) >= 1
        assert_field(results[0], "commission_pct", "3.75")

    def test_tc3_account_name(self):
        results = run_tc_pipeline("test", TC_3)
        assert len(results) >= 1
        assert_field(results[0], "account_name", "DAI AN OCEAN")

    def test_tc3_charter_period(self):
        results = run_tc_pipeline("test", TC_3)
        assert len(results) >= 1
        assert_field(results[0], "charter_period", "1-3 YEARS")

    def test_tc3_commission(self):
        results = run_tc_pipeline("test", TC_3)
        assert len(results) >= 1
        assert_field(results[0], "commission_pct", "3.75")

    def test_tc4_account_name(self):
        results = run_tc_pipeline("test", TC_4)
        assert len(results) >= 1
        assert_field(results[0], "account_name", "SeaSchiffe")

    def test_tc4_delivery_port(self):
        results = run_tc_pipeline("test", TC_4)
        assert len(results) >= 1
        assert_field(results[0], "delivery_port", "ECI")

    def test_tc4_delivery_date(self):
        results = run_tc_pipeline("test", TC_4)
        assert len(results) >= 1
        assert_field(results[0], "delivery_date", "15-18 July")

    def test_tc4_redelivery_port(self):
        results = run_tc_pipeline("test", TC_4)
        assert len(results) >= 1
        assert_field(results[0], "redelivery_port", "Med")

    def test_tc4_charter_period(self):
        results = run_tc_pipeline("test", TC_4)
        assert len(results) >= 1
        assert_field(results[0], "charter_period", "35-40 days")

    def test_tc4_commission(self):
        results = run_tc_pipeline("test", TC_4)
        assert len(results) >= 1
        assert_field(results[0], "commission_pct", "3.75")

    def test_tc4_vessel_dwt(self):
        results = run_tc_pipeline("test", TC_4)
        assert len(results) >= 1
        assert_field(results[0], "vessel_dwt", "22")

    def test_tc5_account_name(self):
        results = run_tc_pipeline("test", TC_5)
        assert len(results) >= 1
        assert_field(results[0], "account_name", "SeaSchiffe")

    def test_tc5_delivery_port(self):
        results = run_tc_pipeline("test", TC_5)
        assert len(results) >= 1
        assert_field(results[0], "delivery_port", "ECI")

    def test_tc5_delivery_date(self):
        results = run_tc_pipeline("test", TC_5)
        assert len(results) >= 1
        assert_field(results[0], "delivery_date", "21-23 July")

    def test_tc5_redelivery_port(self):
        results = run_tc_pipeline("test", TC_5)
        assert len(results) >= 1
        assert_field(results[0], "redelivery_port", "ARAG")

    def test_tc5_charter_period(self):
        results = run_tc_pipeline("test", TC_5)
        assert len(results) >= 1
        assert_field(results[0], "charter_period", "50-55 days")

    def test_tc5_commission(self):
        results = run_tc_pipeline("test", TC_5)
        assert len(results) >= 1
        assert_field(results[0], "commission_pct", "3.75")

    def test_tc5_vessel_dwt(self):
        results = run_tc_pipeline("test", TC_5)
        assert len(results) >= 1
        assert_field(results[0], "vessel_dwt", "33")
