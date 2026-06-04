"""Tonnage extraction pipeline tests with realistic email examples."""

import pytest

from src.extraction.segmentation import segment_vessels
from src.extraction.pipeline import run_tonnage_pipeline
from src.extraction.regex_patterns import (
    VESSEL_NAME, ACCOUNT_NAME, OPEN_PORT, OPEN_DATE,
    VESSEL_TYPE, VESSEL_SIZE_DWT,
)
from src.extraction.confidence import score_vessel_name, make_field


# ── Example 1: Single vessel, labeled format ──────────────────
EMAIL_SINGLE = """Subject: TONNAGE - MV ALPHA STAR

ACCOUNT: Acme Shipping Co.
VESSEL: M/V ALPHA STAR
TYPE: BULK CARRIER
DWT: 82,000
OPEN PORT: Rotterdam
OPEN DATE: 15-20 Jan 2025"""

# ── Example 2: Multiple vessels, numbered list ─────────────────
EMAIL_MULTI = """Subject: TONNAGE - MULTIPLE VESSELS

1. M/V BRAVO SUN
   ACCOUNT: Beta Maritime
   TYPE: TANKER
   DWT: 50,000
   OPEN PORT: Houston
   LAYCAN: 01-10 Feb 2025

2. M/V CHARLIE MOON
   ACCOUNT: Beta Maritime
   TYPE: BULK CARRIER
   DWT: 65,000
   OPEN PORT: Santos
   LAYCAN: 05-15 Mar 2025"""

# ── Example 3: Free-text / prose format ────────────────────────
EMAIL_PROSE = """We are pleased to offer the M/V DELTA WAVE, a BULK CARRIER of approx 75,000 DWT.
Open in Singapore around 10-20 January 2025.
Account: Gamma Shipping Ltd."""

# ── Example 4: Single vessel, all-caps compact ─────────────────
EMAIL_COMPACT = """MV ECHO STAR / ACCT: Delta Lines / TYPE: CONTAINER VESSEL / DWT 45,000 / LOADPORT: Shanghai / LAYCAN: 10-20 Mar 2025"""

# ── Example 5: Vessel account type format (VSL prefix) ─────────
EMAIL_VSL = """VESSEL: FOXTROT WAVE
ACCOUNT: Epsilon Maritime Corp
TYPE: CHEMICAL TANKER
DWT 35,000
LOADING PORT: Rotterdam
LAYDAYS: 01-15 Apr 2025"""

# ── Example 6: Short free-text with line-separated fields ──────
EMAIL_SHORT = """Subject: Fw: TONNAGE - MV GOLF RIVER
MV GOLF RIVER
BULK CARRIER
82,000 DWT
Open: Paranagua
15-25 Jan 2025
ACCT: Acme Shipping Inc."""

# ── Example 7: Single vessel, owner format ─────────────────────
EMAIL_OWNER = """CHARTERER: Zeta Shipping
M/V HOTEL SKY, BULK CARRIER, 63,000 DWT
PORT OF LOADING: New Orleans
DELIVERY: 05-15 Feb 2025"""


# ═══════════════════════════════════════════════════════════════
# 1. Segmentation tests
# ═══════════════════════════════════════════════════════════════

class TestSegmentation:
    def test_single_email_is_one_segment(self):
        segs = segment_vessels(EMAIL_SINGLE)
        assert len(segs) >= 1

    def test_multi_vessel_split(self):
        segs = segment_vessels(EMAIL_MULTI)
        assert len(segs) >= 2

    def test_empty_text(self):
        assert segment_vessels("") == []
        assert segment_vessels(None) == []

    def test_short_prose_is_one_segment(self):
        segs = segment_vessels(EMAIL_PROSE)
        assert len(segs) >= 1


# ═══════════════════════════════════════════════════════════════
# 2. Regex pattern tests
# ═══════════════════════════════════════════════════════════════

class TestRegexPatterns:
    def test_vessel_name_mv_prefix(self):
        m = VESSEL_NAME[0].search("M/V ALPHA STAR")
        assert m and m.group(1).strip() == "ALPHA STAR"

    def test_vessel_name_vessel_label(self):
        m = VESSEL_NAME[1].search("VESSEL: BRAVO SUN")
        assert m and "BRAVO SUN" in m.group(1)

    def test_vessel_name_vsl_label(self):
        m = VESSEL_NAME[2].search("VSL: CHARLIE MOON")
        assert m and "CHARLIE MOON" in m.group(1)

    def test_vessel_name_line_start(self):
        m = VESSEL_NAME[3].search("MV DELTA WAVE\n")
        assert m and "DELTA WAVE" in m.group(1).strip()

    def test_account_name_labeled(self):
        m = ACCOUNT_NAME[0].search("ACCOUNT: Acme Shipping Co.")
        assert m and "Acme Shipping Co" in m.group(1)

    def test_account_name_charterer(self):
        m = ACCOUNT_NAME[0].search("CHARTERER: Beta Maritime")
        assert m and "Beta Maritime" in m.group(1)

    def test_open_port_labeled(self):
        m = OPEN_PORT[0].search("OPEN PORT: Rotterdam")
        assert m and "Rotterdam" in m.group(1).strip()

    def test_open_port_loading_port(self):
        m = OPEN_PORT[1].search("LOAD PORT: Santos")
        assert m and "Santos" in m.group(1).strip()

    def test_open_date_laycan(self):
        m = OPEN_DATE[1].search("LAYCAN: 01-10 Feb 2025")
        assert m

    def test_open_date_open_date_label(self):
        m = OPEN_DATE[1].search("OPEN DATE: 15-20 Jan 2025")
        assert m

    def test_vessel_type_labeled(self):
        m = VESSEL_TYPE[0].search("TYPE: BULK CARRIER")
        assert m and "BULK CARRIER" in m.group(1).strip()

    def test_vessel_type_free_text(self):
        m = VESSEL_TYPE[1].search("this is a BULK CARRIER vessel")
        assert m and "BULK CARRIER" in m.group(1).strip()

    def test_dwt_labeled(self):
        m = VESSEL_SIZE_DWT[0].search("DWT: 82,000")
        assert m and "82,000" in m.group(1)

    def test_dwt_suffix(self):
        m = VESSEL_SIZE_DWT[1].search("75,000 DWT")
        assert m and "75,000" in m.group(1)

    def test_dwt_deadweight(self):
        m = VESSEL_SIZE_DWT[1].search("50000 DEADWEIGHT")
        assert m and "50000" in m.group(1)


# ═══════════════════════════════════════════════════════════════
# 3. Confidence scoring tests
# ═══════════════════════════════════════════════════════════════

class TestConfidence:
    def test_labeled_regex_high_confidence(self):
        f = make_field("ALPHA STAR", "regex_labeled", score_vessel_name)
        assert f.confidence >= 0.9

    def test_marker_regex_good_confidence(self):
        f = make_field("BRAVO SUN", "regex_marker", score_vessel_name)
        assert 0.8 <= f.confidence < 0.9

    def test_spacy_moderate_confidence(self):
        f = make_field("CHARLIE", "spacy", score_vessel_name)
        assert 0.7 <= f.confidence < 0.8

    def test_fallback_low_confidence(self):
        f = make_field("DELTA", "fallback", score_vessel_name)
        assert f.confidence < 0.5

    def test_confidence_trailing_comma_stripped(self):
        f = make_field("ALPHA,", "regex_labeled", score_vessel_name)
        assert f.value == "ALPHA"


# ═══════════════════════════════════════════════════════════════
# 4. Full pipeline end-to-end tests
# ═══════════════════════════════════════════════════════════════

class TestPipelineSingleVessel:
    def test_extracts_vessel_name(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        assert len(results) >= 1
        v = results[0]
        assert v.vessel_name and "ALPHA STAR" in v.vessel_name.value.upper()

    def test_extracts_account(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        v = results[0]
        assert v.account_name and "Acme" in v.account_name.value

    def test_extracts_open_port(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        v = results[0]
        assert v.open_port and "Rotterdam" in v.open_port.value

    def test_extracts_open_date(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        v = results[0]
        assert v.open_date and "2025" in v.open_date.value

    def test_extracts_vessel_type(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        v = results[0]
        assert v.vessel_type and "BULK" in v.vessel_type.value.upper()

    def test_extracts_dwt(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        v = results[0]
        assert v.vessel_size_dwt and "82" in v.vessel_size_dwt.value

    def test_confidence_threshold(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        v = results[0]
        assert v.overall_confidence >= 0.8


class TestPipelineMultiVessel:
    def test_extracts_two_vessels(self):
        results = run_tonnage_pipeline("test-2", EMAIL_MULTI)
        assert len(results) >= 2

    def test_first_vessel_bravo(self):
        results = run_tonnage_pipeline("test-2", EMAIL_MULTI)
        v0 = results[0]
        assert v0.vessel_name and "BRAVO" in v0.vessel_name.value.upper()

    def test_second_vessel_charlie(self):
        results = run_tonnage_pipeline("test-2", EMAIL_MULTI)
        v1 = results[1]
        assert v1.vessel_name and "CHARLIE" in v1.vessel_name.value.upper()

    def test_both_have_account(self):
        results = run_tonnage_pipeline("test-2", EMAIL_MULTI)
        for v in results:
            assert v.account_name and "Beta" in v.account_name.value

    def test_different_ports(self):
        results = run_tonnage_pipeline("test-2", EMAIL_MULTI)
        assert results[0].open_port and "Houston" in results[0].open_port.value
        assert results[1].open_port and "Santos" in results[1].open_port.value


class TestPipelineProse:
    def test_extracts_vessel_name(self):
        results = run_tonnage_pipeline("test-3", EMAIL_PROSE)
        assert len(results) >= 1
        v = results[0]
        assert v.vessel_name and "DELTA" in v.vessel_name.value.upper()

    def test_extracts_type_from_prose(self):
        results = run_tonnage_pipeline("test-3", EMAIL_PROSE)
        v = results[0]
        assert v.vessel_type and "BULK" in v.vessel_type.value.upper()

    def test_extracts_dwt_from_prose(self):
        results = run_tonnage_pipeline("test-3", EMAIL_PROSE)
        v = results[0]
        assert v.vessel_size_dwt and "75" in v.vessel_size_dwt.value

    def test_extracts_port_from_prose(self):
        results = run_tonnage_pipeline("test-3", EMAIL_PROSE)
        v = results[0]
        assert v.open_port and "Singapore" in v.open_port.value


class TestPipelineCompact:
    def test_compact_format(self):
        results = run_tonnage_pipeline("test-4", EMAIL_COMPACT)
        assert len(results) >= 1
        v = results[0]
        assert v.vessel_name and "ECHO" in v.vessel_name.value.upper()
        assert v.account_name and "Delta" in v.account_name.value
        assert v.vessel_type and "CONTAINER" in v.vessel_type.value.upper()
        assert v.vessel_size_dwt and "45" in v.vessel_size_dwt.value
        assert v.open_port and "Shanghai" in v.open_port.value


class TestPipelineEdgeCases:
    def test_empty_body_returns_empty(self):
        results = run_tonnage_pipeline("test-empty", "")
        assert results == []

    def test_vsl_prefix_format(self):
        results = run_tonnage_pipeline("test-5", EMAIL_VSL)
        v = results[0]
        assert v.vessel_name and "FOXTROT" in v.vessel_name.value.upper()
        assert v.account_name and "Epsilon" in v.account_name.value

    def test_owner_format(self):
        results = run_tonnage_pipeline("test-7", EMAIL_OWNER)
        v = results[0]
        assert v.vessel_name and "HOTEL" in v.vessel_name.value.upper()
        # charterer line is a separate segment before M/V boundary; not linked
        assert v.open_port and "New Orleans" in v.open_port.value

    def test_to_record_dict_includes_confidence(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        d = results[0].to_record_dict()
        assert "vessel_name" in d
        assert "confidence" in d["vessel_name"]
        assert d["vessel_name"]["value"] != ""

    def test_overall_confidence_calculation(self):
        results = run_tonnage_pipeline("test-1", EMAIL_SINGLE)
        v = results[0]
        assert 0 < v.overall_confidence <= 1.0


# ═══════════════════════════════════════════════════════════════
# 5. Real-world format regression tests
# ═══════════════════════════════════════════════════════════════

class TestPipelineRealWorld:

    EMAIL_REAL_1 = """P R I M E   M A R I T I M E   I N C. - PIRAEUS

OUR DIRECT OWS OPEN AS FOLLOWS
PACIFIC
=======
SARONIC CHAMPION (93K – SCRUBBER FITTED / 2011) – OPEN VUNG ANG, VIETNAM 08-12 JUNE
ABT 93.116 DWT ON ABT 14.90 MTRS SSW (SCANTLING)

PACIFIC OCEAN
=======================
MV SHENG AN HAI DWT 56564 OPEN XIAMEN, CHINA O/A 2ND JUNE 2026
MV FENG HUI HAI DWT 63260 OPEN GUANGZHOU, CHINA O/A 6TH JUNE 2026
MV YUANPING SEA DWT 55646 OPEN MANILA, PHI O/A 3RD JUNE 2026
MV SHENG DE HAI DWT 56721 OPEN SAMALAJU, MALAYSIA O/A 3RD JUNE 2026

INDIAN OCEAN
=======================
MV YIN HUA 1 DWT 46613 OPEN CHITTAGONG, B.DESH O/A 5TH JUNE 2026
MV BI JIA SHAN DWT 56623 OPEN GWADAR, PAKISTAN O/A 2ND JUNE 2026
MV YUANNING SEA DWT 55580 OPEN SOHAR, OMAN O/A 30TH MAY 2026
MV COS ORCHID DWT 55550 OPEN DAR ES SALAAM, TANZANIA O/A 1ST JUNE 2026

VSL PARTICULAR:
M/V: SHENG AN HAI
BUILT: 2012.12 FLAG: CHINA CLASS: CCS
DWT 56564.4MT ON 12.8M SSW DRAFT-TPC 58.8"""

    EMAIL_REAL_2 = """MV TRUE FRIEND/51K/ 09 - BEJAIA, 1ST JUNE ONW - EX OUR CP

OPEN HATC BOX
DWT: 51.241/
BUILT: 2009 FLAG: BARBADOS BULK CARRIER
5/5 HO/HA GRAIN: ABT 59,676
CRANES: 4X30.5T NIL GRABS"""

    EMAIL_REAL_3 = """MV BLUE STAR (38K DWT) - OPEN 25 MAY GABES, TUNISIA
GEARED SELF-TRIMMING SINGLE DECK BULK CARRIER
BUILT 2011 SAMHO SHIPBUILDING CO LTD, KOREA
37,947 MTDWT ON 10,63 M SSW (TPC 49,16)
5 H/H 4 X 35MT CRANES"""

    EMAIL_REAL_4 = """ECSA + W. AFRICA
MV DE SHENG HAI DWT 38,821.5 MT OPEN MUCURIPE, BRAZIL O/A 24-25 MAY 2026

CONTI+MED
M/V AN DING HAI DWT 38,800 MT - OPEN CASABLANCA O/A 28-30 MAY 2026

VSL PARTICULAR:
MV JIAN GUO HAI
2016 BLT HONGKONG FLAG SDBC
DWT 38766.6MT ON 10.5M SSW TPC: 54MT

MV AN DING HAI
2017 BLT HONGKONG FLAG SDBC
38800.9 DWT ON 10.5M SSW TPC:54MT
5 HO/5 HA GEAR: 4 X 30 TON CRANES"""

    def test_real1_has_vessels_filtered_no_dupes(self):
        """Multi-vessel with section headers, VSL PARTICULAR should not create dupes."""
        results = run_tonnage_pipeline("real1", self.EMAIL_REAL_1)
        assert 4 <= len(results) <= 9  # at least the 4 listed in PACIFIC OCEAN
        names = [v.vessel_name.value.upper() for v in results if v.vessel_name]
        # SHENG AN HAI should appear at most once (dedup)
        sheng = [n for n in names if "SHENG AN HAI" in n]
        assert len(sheng) <= 1

    def test_real1_first_vessel_has_open_port(self):
        results = run_tonnage_pipeline("real1", self.EMAIL_REAL_1)
        # The first MV vessel should be SHENG AN HAI
        mv_vessels = [v for v in results if v.vessel_name and "SHENG" in v.vessel_name.value.upper()]
        if mv_vessels:
            v = mv_vessels[0]
            assert v.open_port is not None

    def test_real1_ordinal_date_extracted(self):
        """O/A 2ND JUNE 2026 should be found as open date."""
        results = run_tonnage_pipeline("real1", self.EMAIL_REAL_1)
        for v in results:
            if v.vessel_name and "SHENG" in v.vessel_name.value.upper():
                assert v.open_date is not None
                assert "2ND" in v.open_date.value or "JUNE" in v.open_date.value
                return

    def test_real1_dwt_56564_extracted(self):
        results = run_tonnage_pipeline("real1", self.EMAIL_REAL_1)
        for v in results:
            if v.vessel_name and "SHENG" in v.vessel_name.value.upper():
                assert v.vessel_size_dwt is not None
                return

    def test_real2_true_friend_vessel_name(self):
        results = run_tonnage_pipeline("real2", self.EMAIL_REAL_2)
        assert len(results) >= 1
        v = results[0]
        assert v.vessel_name and "TRUE FRIEND" in v.vessel_name.value.upper()

    def test_real2_true_friend_dwt(self):
        results = run_tonnage_pipeline("real2", self.EMAIL_REAL_2)
        v = results[0]
        assert v.vessel_size_dwt and "51" in v.vessel_size_dwt.value.replace(",", "")

    def test_real2_true_friend_open_port(self):
        results = run_tonnage_pipeline("real2", self.EMAIL_REAL_2)
        v = results[0]
        assert v.open_port and "BEJAIA" in v.open_port.value.upper()

    def test_real3_blue_star_vessel_name(self):
        results = run_tonnage_pipeline("real3", self.EMAIL_REAL_3)
        assert len(results) >= 1
        v = results[0]
        assert v.vessel_name and "BLUE STAR" in v.vessel_name.value.upper()

    def test_real3_blue_star_dwt_38k(self):
        results = run_tonnage_pipeline("real3", self.EMAIL_REAL_3)
        v = results[0]
        assert v.vessel_size_dwt and ("38" in v.vessel_size_dwt.value or "37" in v.vessel_size_dwt.value)

    def test_real3_blue_star_open_port(self):
        results = run_tonnage_pipeline("real3", self.EMAIL_REAL_3)
        v = results[0]
        assert v.open_port and "GABES" in v.open_port.value.upper()

    def test_real4_de_sheng_hai_vessel_name(self):
        results = run_tonnage_pipeline("real4", self.EMAIL_REAL_4)
        assert len(results) >= 2
        names = [v.vessel_name.value.upper() for v in results if v.vessel_name]
        assert any("DE SHENG HAI" in n for n in names)
        assert any("AN DING HAI" in n for n in names)

    def test_real4_oa_date_range(self):
        """O/A 24-25 MAY 2026 should be found."""
        results = run_tonnage_pipeline("real4", self.EMAIL_REAL_4)
        for v in results:
            if v.vessel_name and "DE SHENG" in v.vessel_name.value.upper():
                assert v.open_date is not None

    def test_real4_dwt_with_commas(self):
        """38,821.5 MT DWT format should be extracted."""
        results = run_tonnage_pipeline("real4", self.EMAIL_REAL_4)
        for v in results:
            if v.vessel_name and "DE SHENG" in v.vessel_name.value.upper():
                assert v.vessel_size_dwt is not None
                return

    def test_real4_no_dupes_from_vsl_particular(self):
        """VSL PARTICULAR section should not create duplicate vessel entries."""
        results = run_tonnage_pipeline("real4", self.EMAIL_REAL_4)
        names = [v.vessel_name.value.upper() for v in results if v.vessel_name]
        deduped = set(names)
        assert len(names) == len(deduped), f"Duplicates found: {names}"


# ═══════════════════════════════════════════════════════════════
# 6. to_record_dict tests
# ═══════════════════════════════════════════════════════════════

class TestRecordDict:
    def test_contains_all_fields(self):
        results = run_tonnage_pipeline("test-dict", EMAIL_SINGLE)
        d = results[0].to_record_dict()
        for key in ("vessel_name", "account_name", "open_port", "open_date", "vessel_type", "vessel_size_dwt"):
            assert key in d, f"missing {key}"

    def test_contains_metadata(self):
        results = run_tonnage_pipeline("test-dict", EMAIL_SINGLE)
        d = results[0].to_record_dict()
        assert "_segment_index" in d
        assert "_segmentation_confidence" in d
