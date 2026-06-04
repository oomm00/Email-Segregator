"""Cargo VC extraction pipeline tests with realistic email examples."""

import pytest

from src.extraction_cargo.segmentation import segment_cargoes
from src.extraction_cargo.pipeline import run_cargo_vc_pipeline
from src.extraction_cargo.regex_patterns import (
    ACCOUNT_NAME, CARGO_NAME, LOADING_PORT, DISCHARGE_PORT,
    LAYCAN, CARGO_TYPE, QUANTITY, LOAD_RATE, DISCHARGE_RATE,
    COMMISSION,
)
from src.extraction_cargo.confidence import (
    make_field, score_account_name, score_cargo_name,
    score_loading_port, score_laycan, score_quantity,
)


# ── Example 1: Single cargo, full labeled format ─────────────
EMAIL_SINGLE = """ACCOUNT: Oceanic Bulk Carriers
CARGO: SOYBEANS
LOAD PORT: TUBARAO
DISCHARGE PORT: ROTTERDAM
LAYCAN: 15-20 MAR 2025
CARGO TYPE: AGRICULTURAL
QUANTITY: 60,000 MT
LOADING RATE: 10,000 MT PWWD SSHEX
DISCHARGE RATE: 6,000 MT PWWD SHEX
COMM: 2.5%"""

# ── Example 2: Multiple cargoes, numbered list ────────────────
EMAIL_MULTI = """1. CARGO: IRON ORE
   ACCOUNT: Vale Shipping
   POL: TUBARAO
   POD: QINGDAO
   LAYCAN: 01-10 APR 2025
   QTY: 150,000 MT
   TYPE: FINES
   LOADRATE: 12,000
   DISCHRATE: 8,000
   COMM: 1.25%

2. CARGO: BAUXITE
   ACCOUNT: Vale Shipping
   LP: ITAGUAI
   DP: ZHUHAI
   LAYCAN: 15-25 APR 2025
   QTY: 80,000 MT
   COMM: 1.25%"""

# ── Example 3: Prose format ──────────────────────────────────
EMAIL_PROSE = """We are pleased to offer a cargo of CRUDE OIL for the account of PetroGlobal.
Loading port: Ras Tanura, discharge port: Rotterdam.
Laycan 20-30 March 2025, quantity approx 100,000 MT.
Loading rate 8,000 MT PWWD, discharging rate 5,000 MT PWWD.
Commission 2.5% TTL."""

# ── Example 4: Compact / forward-slash format ─────────────────
EMAIL_COMPACT = """ACCT: Atlantic Trading / CARGO: GAS OIL / LP: HOUSTON / DP: SINGAPORE / LAYCAN: 05-15 JUN 2025 / QTY: 45,000 MT / COMM: 1.5% / TYPE: CLEAN"""

# ── Example 5: PWWD + FIOS / CQD format ──────────────────────
EMAIL_PWWD = """CHARTERER: Gulf Energy
COMMODITY: FUEL OIL
LOAD PORT: FUJAIRAH
DISCHARGE PORT: SINGAPORE
LAYCAN: 10-20 MAY 2025
QUANTITY: 80,000 MT (5% MOLOO)
LOAD RATE: 12,000 MT PWWD SSHEX
DISCH RATE: 8,000 MT PWWD SHEX
COM: 1.25%
CQD IF USED"""

# ── Example 6: Short format ──────────────────────────────────
EMAIL_SHORT = """CARGO: WHEAT
ACCT: Midgrain Corp
POL: NEMRUT
POD: ALEXANDRIA
LAYCAN: 01-10 JUL 2025
QTY: 35,000 MT
COMM: 2.5%"""

# ── Example 7: Owner/Charterer format ─────────────────────────
EMAIL_OWNER = """OWNER: Scandinavian Tankers
CARGO: NAPHTHA
PORT OF LOADING: STAVANGER
DESTINATION: PORT ARTHUR
DELIVERY: 05-15 SEP 2025
QUANTITY: 55,000 MT
LOADING RATE: 9,000 MT
COM: 1.75%"""

# ── Example 8: Product label ─────────────────────────────────
EMAIL_PRODUCT = """PRODUCT: SOYBEAN MEAL
ACCOUNT: Cargill Intl
LOADING PORT: PARANAGUA
DISCHARGE PORT: JEDDAH
LAYCAN: 20-30 AUG 2025
QTY: 25,000-30,000 MT
COMMISSION: 3.75%
TYPE: BULK AGRI"""

# ── Example 9: Single cargo multiple accounts format ─────────
EMAIL_SINGLE_ACCT = """CHARTERER: BHP Billiton
CARGO: COKING COAL
POL: HAY POINT
POD: ROTTERDAM
LAYCAN: 10-20 NOV 2025
QUANTITY: 75,000 MT
LOAD RATE: 15,000 MT
DISCH RATE: 10,000 MT
COM: 2%"""

# ── Example 10: Quantity range only ──────────────────────────
EMAIL_QTY_RANGE = """ACCT: Glencore Agri
CARGO: CORN
LP: MYRTLE GROVE
DP: KEELUNG
LAYCAN: 05-15 DEC 2025
MIN/MAX: 30,000 / 40,000 MT
COMM: 1.5%"""


# ═══════════════════════════════════════════════════════════════
# 1. Segmentation tests
# ═══════════════════════════════════════════════════════════════

class TestSegmentation:
    def test_single_email_is_one_segment(self):
        segs = segment_cargoes(EMAIL_SINGLE)
        assert len(segs) >= 1

    def test_multi_cargo_split(self):
        segs = segment_cargoes(EMAIL_MULTI)
        assert len(segs) >= 2

    def test_empty_text(self):
        assert segment_cargoes("") == []
        assert segment_cargoes(None) == []

    def test_prose_is_one_segment(self):
        segs = segment_cargoes(EMAIL_PROSE)
        assert len(segs) >= 1

    def test_short_format_one_segment(self):
        segs = segment_cargoes(EMAIL_SHORT)
        assert len(segs) >= 1

    def test_pwwd_format_one_segment(self):
        segs = segment_cargoes(EMAIL_PWWD)
        assert len(segs) >= 1


# ═══════════════════════════════════════════════════════════════
# 2. Regex pattern tests
# ═══════════════════════════════════════════════════════════════

class TestRegexPatterns:
    def test_account_name_labeled(self):
        m = ACCOUNT_NAME[0].search("ACCOUNT: Oceanic Bulk Carriers")
        assert m and "Oceanic Bulk Carriers" in m.group(1)

    def test_account_name_charterer(self):
        m = ACCOUNT_NAME[0].search("CHARTERER: Gulf Energy")
        assert m and "Gulf Energy" in m.group(1)

    def test_account_name_owner(self):
        m = ACCOUNT_NAME[0].search("OWNER: Scandinavian Tankers")
        assert m and "Scandinavian Tankers" in m.group(1)

    def test_account_name_acct_abbrev(self):
        m = ACCOUNT_NAME[0].search("ACCT: Atlantic Trading")
        assert m and "Atlantic Trading" in m.group(1)

    def test_cargo_name_labeled(self):
        m = CARGO_NAME[0].search("CARGO: SOYBEANS")
        assert m and "SOYBEANS" in m.group(1).strip()

    def test_cargo_name_commodity(self):
        m = CARGO_NAME[0].search("COMMODITY: CRUDE OIL")
        assert m and "CRUDE OIL" in m.group(1).strip()

    def test_cargo_name_product(self):
        m = CARGO_NAME[0].search("PRODUCT: SOYBEAN MEAL")
        assert m and "SOYBEAN MEAL" in m.group(1).strip()

    def test_loading_port_labeled(self):
        m = LOADING_PORT[0].search("LOAD PORT: TUBARAO")
        assert m and "TUBARAO" in m.group(1).strip()

    def test_loading_port_pol(self):
        m = LOADING_PORT[0].search("POL: ITAGUAI")
        assert m and "ITAGUAI" in m.group(1).strip()

    def test_loading_port_lp(self):
        m = LOADING_PORT[0].search("LP: HOUSTON")
        assert m and "HOUSTON" in m.group(1).strip()

    def test_discharge_port_labeled(self):
        m = DISCHARGE_PORT[0].search("DISCHARGE PORT: ROTTERDAM")
        assert m and "ROTTERDAM" in m.group(1).strip()

    def test_discharge_port_pod(self):
        m = DISCHARGE_PORT[0].search("POD: QINGDAO")
        assert m and "QINGDAO" in m.group(1).strip()

    def test_discharge_port_dp(self):
        m = DISCHARGE_PORT[0].search("DP: SINGAPORE")
        assert m and "SINGAPORE" in m.group(1).strip()

    def test_discharge_port_dest(self):
        m = DISCHARGE_PORT[0].search("DESTINATION: PORT ARTHUR")
        assert m and "PORT ARTHUR" in m.group(1).strip()

    def test_laycan_full(self):
        m = LAYCAN[1].search("LAYCAN: 15-20 MAR 2025")
        assert m

    def test_laycan_pwwd(self):
        m = LAYCAN[1].search("PWWD: 10-20 MAY 2025")
        assert m

    def test_laycan_delivery(self):
        m = LAYCAN[1].search("DELIVERY: 05-15 SEP 2025")
        assert m

    def test_cargo_type_labeled(self):
        m = CARGO_TYPE[0].search("TYPE: AGRICULTURAL")
        assert m and "AGRICULTURAL" in m.group(1).strip()

    def test_quantity_single(self):
        m = QUANTITY[0].search("QUANTITY: 60,000 MT")
        assert m and "60,000" in m.group(1)

    def test_quantity_with_range(self):
        m = QUANTITY[0].search("QTY: 25,000-30,000 MT")
        assert m and "25,000" in m.group(1)
        assert m.lastindex and m.lastindex >= 2 and m.group(2) == "30,000"

    def test_quantity_min_max(self):
        m = QUANTITY[0].search("MIN/MAX: 30,000 / 40,000 MT")
        assert m and "30,000" in m.group(1)
        assert m.lastindex and m.lastindex >= 2 and "40,000" in m.group(2)

    def test_load_rate_labeled(self):
        m = LOAD_RATE[0].search("LOADING RATE: 10,000 MT PWWD SSHEX")
        assert m and "10,000" in m.group(1)

    def test_load_rate_short(self):
        m = LOAD_RATE[0].search("LOAD RATE: 8,000 MT PWWD")
        assert m and "8,000" in m.group(1)

    def test_loadrate_compact(self):
        m = LOAD_RATE[0].search("LOADRATE: 12,000")
        assert m and "12,000" in m.group(1)

    def test_discharge_rate_labeled(self):
        m = DISCHARGE_RATE[0].search("DISCHARGE RATE: 6,000 MT PWWD SHEX")
        assert m and "6,000" in m.group(1)

    def test_dischrate_compact(self):
        m = DISCHARGE_RATE[0].search("DISCHRATE: 8,000")
        assert m and "8,000" in m.group(1)

    def test_commission_colon(self):
        m = COMMISSION[0].search("COMM: 2.5%")
        assert m and "2.5" in m.group(1)

    def test_commission_full(self):
        m = COMMISSION[0].search("COMMISSION: 3.75%")
        assert m and "3.75" in m.group(1)

    def test_commission_brokerage(self):
        m = COMMISSION[0].search("BROKERAGE: 1.5%")
        assert m and "1.5" in m.group(1)

    def test_commission_ttl(self):
        m = COMMISSION[0].search("TTL: 1.25%")
        assert m and "1.25" in m.group(1)

    def test_commission_suffix_format(self):
        m = COMMISSION[1].search("2.5% COMM")
        assert m and "2.5" in m.group(1)


# ═══════════════════════════════════════════════════════════════
# 3. Confidence tests
# ═══════════════════════════════════════════════════════════════

class TestConfidence:
    def test_labeled_regex_high_confidence(self):
        f = make_field("Oceanic Bulk", "regex_labeled", score_account_name)
        assert f.confidence >= 0.85

    def test_spacy_moderate_confidence(self):
        f = make_field("Cargill", "spacy", score_cargo_name)
        assert 0.65 <= f.confidence < 0.8

    def test_fallback_low_confidence(self):
        f = make_field("Some Cargo", "fallback", score_account_name)
        assert f.confidence < 0.5

    def test_laycan_regex_high(self):
        f = make_field("15-20 MAR 2025", "regex_labeled", score_laycan)
        assert f.confidence >= 0.9

    def test_quantity_reasonable_confidence(self):
        f = make_field("60,000", "regex_labeled", score_quantity)
        assert f.confidence >= 0.85

    def test_confidence_trailing_comma_stripped(self):
        f = make_field("60,000,", "regex_labeled", score_quantity)
        assert f.value == "60,000"


# ═══════════════════════════════════════════════════════════════
# 4. Full pipeline end-to-end tests
# ═══════════════════════════════════════════════════════════════

class TestPipelineSingleCargo:
    def test_extracts_account(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        assert len(results) >= 1
        c = results[0]
        assert c.account_name and "Oceanic" in c.account_name.value

    def test_extracts_cargo_name(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.cargo_name and "SOYBEANS" in c.cargo_name.value.upper()

    def test_extracts_loading_port(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.loading_port and "TUBARAO" in c.loading_port.value.upper()

    def test_extracts_discharge_port(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.discharge_port and "ROTTERDAM" in c.discharge_port.value.upper()

    def test_extracts_laycan(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.laycan and "2025" in c.laycan.value

    def test_extracts_cargo_type(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.cargo_type and "AGRICULTURAL" in c.cargo_type.value.upper()

    def test_extracts_quantity(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.quantity_min_mt and "60" in c.quantity_min_mt.value.replace(",", "")

    def test_extracts_load_rate(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.load_rate and "10,000" in c.load_rate.value

    def test_extracts_discharge_rate(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.discharge_rate and "6,000" in c.discharge_rate.value

    def test_extracts_commission(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.commission_pct and "2.5" in c.commission_pct.value

    def test_confidence_threshold(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert c.overall_confidence >= 0.8


class TestPipelineMultiCargo:
    def test_extracts_two_cargoes(self):
        results = run_cargo_vc_pipeline("test-2", EMAIL_MULTI)
        assert len(results) >= 2

    def test_first_cargo_iron_ore(self):
        results = run_cargo_vc_pipeline("test-2", EMAIL_MULTI)
        c0 = results[0]
        assert c0.cargo_name and "IRON" in c0.cargo_name.value.upper()

    def test_second_cargo_bauxite(self):
        results = run_cargo_vc_pipeline("test-2", EMAIL_MULTI)
        c1 = results[1]
        assert c1.cargo_name and "BAUXITE" in c1.cargo_name.value.upper()

    def test_both_have_account(self):
        results = run_cargo_vc_pipeline("test-2", EMAIL_MULTI)
        for c in results:
            assert c.account_name and "Vale" in c.account_name.value

    def test_different_ports(self):
        results = run_cargo_vc_pipeline("test-2", EMAIL_MULTI)
        assert results[0].loading_port and "TUBARAO" in results[0].loading_port.value.upper()
        assert results[1].loading_port and "ITAGUAI" in results[1].loading_port.value.upper()


class TestPipelineProse:
    def test_extracts_cargo_from_prose(self):
        results = run_cargo_vc_pipeline("test-3", EMAIL_PROSE)
        assert len(results) >= 1
        c = results[0]
        assert c.cargo_name and "CRUDE" in c.cargo_name.value.upper()

    def test_extracts_port_from_prose(self):
        results = run_cargo_vc_pipeline("test-3", EMAIL_PROSE)
        c = results[0]
        assert c.loading_port and "Ras" in c.loading_port.value
        assert c.discharge_port and "Rotterdam" in c.discharge_port.value

    def test_extracts_laycan_from_prose(self):
        results = run_cargo_vc_pipeline("test-3", EMAIL_PROSE)
        c = results[0]
        assert c.laycan and "2025" in c.laycan.value


class TestPipelineCompact:
    def test_compact_format_all_fields(self):
        results = run_cargo_vc_pipeline("test-4", EMAIL_COMPACT)
        assert len(results) >= 1
        c = results[0]
        assert c.account_name and "Atlantic" in c.account_name.value
        assert c.cargo_name and "GAS OIL" in c.cargo_name.value.upper()
        assert c.loading_port and "HOUSTON" in c.loading_port.value.upper()
        assert c.discharge_port and "SINGAPORE" in c.discharge_port.value.upper()
        assert c.quantity_min_mt and "45" in c.quantity_min_mt.value.replace(",", "")
        assert c.commission_pct and "1.5" in c.commission_pct.value


class TestPipelineEdgeCases:
    def test_empty_body_returns_empty(self):
        results = run_cargo_vc_pipeline("test-empty", "")
        assert results == []

    def test_pwwd_format(self):
        results = run_cargo_vc_pipeline("test-5", EMAIL_PWWD)
        v = results[0]
        assert v.cargo_name and "FUEL" in v.cargo_name.value.upper()
        assert v.loading_port and "FUJAIRAH" in v.loading_port.value.upper()

    def test_owner_format(self):
        results = run_cargo_vc_pipeline("test-7", EMAIL_OWNER)
        v = results[0]
        assert v.account_name and "Scandinavian" in v.account_name.value
        assert v.cargo_name and "NAPHTHA" in v.cargo_name.value.upper()
        assert v.loading_port and "STAVANGER" in v.loading_port.value.upper()

    def test_product_label(self):
        results = run_cargo_vc_pipeline("test-8", EMAIL_PRODUCT)
        v = results[0]
        assert v.cargo_name and "SOYBEAN MEAL" in v.cargo_name.value.upper()
        assert v.commission_pct and "3.75" in v.commission_pct.value
        assert v.cargo_type and "BULK" in v.cargo_type.value.upper()

    def test_quantity_range(self):
        results = run_cargo_vc_pipeline("test-10", EMAIL_QTY_RANGE)
        v = results[0]
        assert v.quantity_min_mt and v.quantity_max_mt
        assert v.quantity_min_mt.value != v.quantity_max_mt.value

    def test_charterer_single_cargo(self):
        results = run_cargo_vc_pipeline("test-9", EMAIL_SINGLE_ACCT)
        v = results[0]
        assert v.account_name and "BHP" in v.account_name.value
        assert v.cargo_name and "COKING" in v.cargo_name.value.upper()
        assert v.loading_port and "HAY POINT" in v.loading_port.value.upper()
        assert v.discharge_port and "ROTTERDAM" in v.discharge_port.value.upper()
        assert v.load_rate and "15,000" in v.load_rate.value
        assert v.discharge_rate and "10,000" in v.discharge_rate.value

    def test_overall_confidence_calculation(self):
        results = run_cargo_vc_pipeline("test-1", EMAIL_SINGLE)
        c = results[0]
        assert 0 < c.overall_confidence <= 1.0


# ═══════════════════════════════════════════════════════════════
# 5. Real-world format regression tests
# ═══════════════════════════════════════════════════════════════

class TestPipelineVCRealWorld:

    VC_1 = """GOOD DAY
PLEASE OFFER FIRM FOR FOLL FULY FIRM CARGO
15,000 - 20,000 MTS 10PCT MOLOCHOPT
LOAD PORT: KOH SI CHANG, THAILAND
DISCHARGE PORT: KANDLA + CHENNAI
LOAD RATE: 1,000 MTS PWWD SSHEX
DISCHARGE RATE: 1500 MTS PWWD SSHEX
LAYCAN: MID JULY 2026
COM: 3.75 PCT TTL"""

    VC_2 = """MCD LIDOMAR
Jeddah / Bilbao
20 000 mt HRC max 28,5 mt
FIOS 4000 mt fhinc / CQD disch
25 June - 5 July try later
3,75% here"""

    VC_3 = """PLS OFFER FIRM FOR FOLL OUR CLOSE AND DIR CHRTRS
20-30,000 mts iron slag in bulk
LP:Bushehr
DP: Doha
10000/12000
25-30 july
3.75% TTL"""

    VC_4 = """Cargo:30,000 mts of Urea in bulk
POL: BIk
POD: Iskenderun or Durban
5000/5000
LAYCAN: 16-20 July
COMM:1.25% TTL"""

    def test_vc1_extracts_cargo(self):
        results = run_cargo_vc_pipeline("vc1", self.VC_1)
        assert len(results) >= 1

    def test_vc1_cargo_name(self):
        results = run_cargo_vc_pipeline("vc1", self.VC_1)
        c = results[0]
        assert c.cargo_name and "MOLOCHOPT" in c.cargo_name.value.upper()

    def test_vc1_loading_port(self):
        results = run_cargo_vc_pipeline("vc1", self.VC_1)
        c = results[0]
        assert c.loading_port and "KOH SI CHANG" in c.loading_port.value.upper()

    def test_vc1_discharge_port(self):
        results = run_cargo_vc_pipeline("vc1", self.VC_1)
        c = results[0]
        assert c.discharge_port and "KANDLA" in c.discharge_port.value.upper()

    def test_vc1_laycan_mid_july(self):
        results = run_cargo_vc_pipeline("vc1", self.VC_1)
        c = results[0]
        assert c.laycan and "MID JULY 2026" in c.laycan.value.upper()

    def test_vc1_quantity(self):
        results = run_cargo_vc_pipeline("vc1", self.VC_1)
        c = results[0]
        assert c.quantity_min_mt and "15000" in c.quantity_min_mt.value.replace(",", "")

    def test_vc1_commission(self):
        results = run_cargo_vc_pipeline("vc1", self.VC_1)
        c = results[0]
        assert c.commission_pct and "3.75" in c.commission_pct.value

    def test_vc2_cargo_name(self):
        """HRC = Hot Rolled Coils"""
        results = run_cargo_vc_pipeline("vc2", self.VC_2)
        assert len(results) >= 1
        c = results[0]
        assert c.cargo_name and "HRC" in c.cargo_name.value.upper()

    def test_vc2_loading_port_jeddah(self):
        results = run_cargo_vc_pipeline("vc2", self.VC_2)
        c = results[0]
        assert c.loading_port and "Jeddah" in c.loading_port.value

    def test_vc2_discharge_port_bilbao(self):
        results = run_cargo_vc_pipeline("vc2", self.VC_2)
        c = results[0]
        assert c.discharge_port and "Bilbao" in c.discharge_port.value

    def test_vc2_laycan_june_july(self):
        results = run_cargo_vc_pipeline("vc2", self.VC_2)
        c = results[0]
        assert c.laycan is not None

    def test_vc2_commission(self):
        results = run_cargo_vc_pipeline("vc2", self.VC_2)
        c = results[0]
        assert c.commission_pct and "3.75" in c.commission_pct.value

    def test_vc3_cargo_name_iron_slag(self):
        results = run_cargo_vc_pipeline("vc3", self.VC_3)
        assert len(results) >= 1
        c = results[0]
        assert c.cargo_name and "iron slag" in c.cargo_name.value.lower()

    def test_vc3_loading_port_bushehr(self):
        results = run_cargo_vc_pipeline("vc3", self.VC_3)
        c = results[0]
        assert c.loading_port and "Bushehr" in c.loading_port.value

    def test_vc3_discharge_port_doha(self):
        results = run_cargo_vc_pipeline("vc3", self.VC_3)
        c = results[0]
        assert c.discharge_port and "Doha" in c.discharge_port.value

    def test_vc3_quantity(self):
        results = run_cargo_vc_pipeline("vc3", self.VC_3)
        c = results[0]
        assert c.quantity_min_mt and "20000" in c.quantity_min_mt.value.replace(",", "")

    def test_vc3_laycan_lowercase(self):
        """25-30 july with lowercase month"""
        results = run_cargo_vc_pipeline("vc3", self.VC_3)
        c = results[0]
        assert c.laycan is not None

    def test_vc3_commission(self):
        results = run_cargo_vc_pipeline("vc3", self.VC_3)
        c = results[0]
        assert c.commission_pct and "3.75" in c.commission_pct.value

    def test_vc4_cargo_name_urea(self):
        results = run_cargo_vc_pipeline("vc4", self.VC_4)
        assert len(results) >= 1
        c = results[0]
        assert c.cargo_name and "Urea" in c.cargo_name.value

    def test_vc4_loading_port_bik(self):
        results = run_cargo_vc_pipeline("vc4", self.VC_4)
        c = results[0]
        assert c.loading_port and "BIk" in c.loading_port.value

    def test_vc4_discharge_port_iskenderun(self):
        results = run_cargo_vc_pipeline("vc4", self.VC_4)
        c = results[0]
        assert c.discharge_port and "Iskenderun" in c.discharge_port.value

    def test_vc4_laycan(self):
        results = run_cargo_vc_pipeline("vc4", self.VC_4)
        c = results[0]
        assert c.laycan is not None

    def test_vc4_commission_no_space(self):
        """COMM:1.25% — no space after colon"""
        results = run_cargo_vc_pipeline("vc4", self.VC_4)
        c = results[0]
        assert c.commission_pct and "1.25" in c.commission_pct.value


# ═══════════════════════════════════════════════════════════════
# 6. to_record_dict tests
# ═══════════════════════════════════════════════════════════════

class TestRecordDict:
    def test_contains_all_fields(self):
        results = run_cargo_vc_pipeline("test-dict", EMAIL_SINGLE)
        d = results[0].to_record_dict()
        for key in (
            "account_name", "cargo_name", "loading_port", "discharge_port",
            "laycan", "cargo_type", "quantity_min_mt", "load_rate",
            "discharge_rate", "commission_pct",
        ):
            assert key in d, f"missing {key}"

    def test_contains_metadata(self):
        results = run_cargo_vc_pipeline("test-dict", EMAIL_SINGLE)
        d = results[0].to_record_dict()
        assert "_segment_index" in d
        assert "_segmentation_confidence" in d


# ═══════════════════════════════════════════════════════════════
# 6. Validation layer tests
# ═══════════════════════════════════════════════════════════════

class TestValidation:
    def test_commission_above_100_removed(self):
        from src.extraction_cargo.validation import validate_extraction
        from src.extraction_cargo.models import CargoVcExtraction, ExtractedField
        c = CargoVcExtraction(
            commission_pct=ExtractedField(value="150", confidence=0.9, method="regex_labeled"),
            cargo_name=ExtractedField(value="Test", confidence=0.9, method="regex_labeled"),
        )
        v = validate_extraction(c)
        assert v.commission_pct is None

    def test_commission_negative_removed(self):
        from src.extraction_cargo.validation import validate_extraction
        from src.extraction_cargo.models import CargoVcExtraction, ExtractedField
        c = CargoVcExtraction(
            commission_pct=ExtractedField(value="-5", confidence=0.9, method="regex_labeled"),
            cargo_name=ExtractedField(value="Test", confidence=0.9, method="regex_labeled"),
        )
        v = validate_extraction(c)
        assert v.commission_pct is None

    def test_same_port_clears_discharge(self):
        from src.extraction_cargo.validation import validate_extraction
        from src.extraction_cargo.models import CargoVcExtraction, ExtractedField
        c = CargoVcExtraction(
            loading_port=ExtractedField(value="Rotterdam", confidence=0.9, method="regex_labeled"),
            discharge_port=ExtractedField(value="ROTTERDAM", confidence=0.9, method="regex_labeled"),
            cargo_name=ExtractedField(value="Test", confidence=0.9, method="regex_labeled"),
        )
        v = validate_extraction(c)
        assert v.discharge_port is None

    def test_cargo_name_type_identical_clears_type(self):
        from src.extraction_cargo.validation import validate_extraction
        from src.extraction_cargo.models import CargoVcExtraction, ExtractedField
        c = CargoVcExtraction(
            cargo_name=ExtractedField(value="IRON ORE", confidence=0.9, method="regex_labeled"),
            cargo_type=ExtractedField(value="IRON ORE", confidence=0.9, method="regex_labeled"),
        )
        v = validate_extraction(c)
        assert v.cargo_type is None
