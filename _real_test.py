"""Real-world email pipeline test — run all three extraction pipelines and matching."""
import json, sys
sys.path.insert(0, ".")

from src.extraction.pipeline import run_tonnage_pipeline
from src.extraction_cargo.pipeline import run_cargo_vc_pipeline
from src.extraction_tc.pipeline import run_tc_pipeline
from src.matching.main import MatchingEngine


# ── TONNAGE EMAILS ─────────────────────────────────────────

TONNAGE_1 = """P R I M E   M A R I T I M E   I N C. - PIRAEUS

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
DWT 56564.4MT ON 12.8M SSW DRAFT-TPC 58.8
HO/HA: 5/5 GRAIN 71634.09CBM

SPD/CONS:
BALLAST: ABT 12.5 KNOTS ON 23 MT LSFO 380
LADEN: ABT 12 KNOTS ON 24 MT LSFO 380
PORT IDLE: ABT 2.8 MT /LSFO 0.05MT/MGO PER DAY

MV FENG HUI HAI
2017 BLT HONG KONG FLAG SDSTBC
63260.8 DWT ON 13.30 M SSW TPC=62.3T/CM
5 HO/5 HA 78771.0 /73430CBM GRAIN/BALE CAPACITY

MV SHENG DE HAI
IMO NO.9663178 CALL SIGN: BPNY
FLAG: PRC CLASS: CCS
SUMMER DWT:56704.2MT DRAFT:12.8M TPC:58.8
GRAIN CAPACITY: 71634.1CBM
TYPE: BULK CARRIER NUMBER OF HATCH: 5

MV YIN HUA 1
2013 BLT CHINA FLAG SDBC
DWT 46613 MT ON 10.90 M SSW TPC 57.7
5 HO/HA 60276.1 CBM GRAIN CAPACITY"""

TONNAGE_2 = """MV TRUE FRIEND/51K/ 09 - BEJAIA, 1ST JUNE ONW - EX OUR CP

OPEN HATC BOX
DWT: 51.241/
BUILT: 2009 FLAG: BARBADOS BULK CARRIER
5/5 HO/HA GRAIN: ABT 59,676
CRANES: 4X30.5T NIL GRABS"""

TONNAGE_3 = """MV BLUE STAR (38K DWT) - OPEN 25 MAY GABES, TUNISIA
GEARED SELF-TRIMMING SINGLE DECK BULK CARRIER
BUILT 2011 SAMHO SHIPBUILDING CO LTD, KOREA
LIBERIAN FLAG / CLASSED HIGHEST ABS
37,947 MTDWT ON 10,63 M SSW (TPC 49,16)
5 H/H 4 X 35MT CRANES"""

TONNAGE_4 = """ECSA + W. AFRICA
MV DE SHENG HAI DWT 38,821.5 MT OPEN MUCURIPE, BRAZIL O/A 24-25 MAY 2026

CONTI+MED
M/V AN DING HAI DWT 38,800 MT - OPEN CASABLANCA O/A 28-30 MAY 2026

VSL PARTICULAR:
MV JIAN GUO HAI
2016 BLT HONGKONG FLAG SDBC
DWT 38766.6MT ON 10.5M SSW TPC: 54MT
5 HO/5 HA GEAR: 4 X 30 TON CRANES

MV AN DING HAI
2017 BLT HONGKONG FLAG SDBC
38800.9 DWT ON 10.5M SSW TPC:54MT
5 HO/5 HA GEAR: 4 X 30 TON CRANES"""

# ── VC CARGO EMAILS ────────────────────────────────────────

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

# ── TC CARGO EMAILS ─────────────────────────────────────────

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


def fmt(v):
    if v is None:
        return "MISSING"
    return f"{v.value} (c:{v.confidence}, m:{v.method})"


def fmt(v):
    if v is None:
        return "MISSING"
    return "%s (c:%.2f, m:%s)" % (v.value, v.confidence, v.method)


def run_tonnage(name, body, subject=""):
    results = run_tonnage_pipeline("test", body, subject)
    print("\n%s" % ("=" * 60))
    print("TONNAGE: %s -- %d vessel(s)" % (name, len(results)))
    if not results:
        print("  ** NO VESSELS EXTRACTED")
        return
    for i, v in enumerate(results):
        print("\n  Vessel %d:" % (i + 1))
        print("    account:     %s" % fmt(v.account_name))
        print("    vessel:      %s" % fmt(v.vessel_name))
        print("    open_port:   %s" % fmt(v.open_port))
        print("    open_date:   %s" % fmt(v.open_date))
        print("    vessel_type: %s" % fmt(v.vessel_type))
        print("    dwt:         %s" % fmt(v.vessel_size_dwt))
        print("    confidence:  %.2f" % v.overall_confidence)


def run_vc(name, body):
    results = run_cargo_vc_pipeline("test", body)
    print("\n%s" % ("=" * 60))
    print("VC CARGO: %s -- %d cargo(es)" % (name, len(results)))
    if not results:
        print("  ** NO CARGOES EXTRACTED")
        return
    for i, c in enumerate(results):
        print("\n  Cargo %d:" % (i + 1))
        for fld in ["account_name","cargo_name","loading_port","discharge_port","laycan",
                     "cargo_type","quantity_min_mt","quantity_max_mt","load_rate","discharge_rate","commission_pct"]:
            val = getattr(c, fld)
            print("    %20s %s" % (fld, fmt(val)))
        print("    %20s %.2f" % ("confidence:", c.overall_confidence))


def run_tc(name, body):
    results = run_tc_pipeline("test", body)
    print("\n%s" % ("=" * 60))
    print("TC CARGO: %s -- %d fixture(s)" % (name, len(results)))
    if not results:
        print("  ** NO TC FIXTURES EXTRACTED")
        return
    for i, tc in enumerate(results):
        print("\n  Fixture %d:" % (i + 1))
        for fld in ["account_name","vessel_name","delivery_port","delivery_date",
                     "redelivery_port","redelivery_date","charter_period","hire_rate",
                     "commission_pct","intended_cargo","vessel_dwt"]:
            val = getattr(tc, fld)
            print("    %20s %s" % (fld, fmt(val)))
        print("    %20s %.2f" % ("confidence:", tc.overall_confidence))


if __name__ == "__main__":
    run_tonnage("Prime Maritime multi", TONNAGE_1)
    run_tonnage("True Friend single", TONNAGE_2)
    run_tonnage("Blue Star single", TONNAGE_3)
    run_tonnage("De Sheng Hai / An Ding Hai", TONNAGE_4)

    run_vc("Cargo 1 (Koh Si Chang)", VC_1)
    run_vc("Cargo 2 (Lidomar)", VC_2)
    run_vc("Cargo 3 (iron slag)", VC_3)
    run_vc("Cargo 4 (Urea)", VC_4)

    run_tc("TC 1 (Dai An / Vancouver)", TC_1)
    run_tc("TC 2 (Dai An / Sangatta)", TC_2)
    run_tc("TC 3 (Dai An / worldwide)", TC_3)
    run_tc("TC 4 (SeaSchiffe 22k)", TC_4)
    run_tc("TC 5 (SeaSchiffe 33k)", TC_5)

    # ── MATCHING ─────────────────────────────────────────────
    vessels = []
    vessels.extend(run_tonnage_pipeline("test", TONNAGE_1))
    vessels.extend(run_tonnage_pipeline("test", TONNAGE_2))
    vessels.extend(run_tonnage_pipeline("test", TONNAGE_3))
    vessels.extend(run_tonnage_pipeline("test", TONNAGE_4))

    cargoes = []
    cargoes.extend(run_cargo_vc_pipeline("test", VC_1))
    cargoes.extend(run_cargo_vc_pipeline("test", VC_2))
    cargoes.extend(run_cargo_vc_pipeline("test", VC_3))
    cargoes.extend(run_cargo_vc_pipeline("test", VC_4))

    fixtures = []
    fixtures.extend(run_tc_pipeline("test", TC_1))
    fixtures.extend(run_tc_pipeline("test", TC_2))
    fixtures.extend(run_tc_pipeline("test", TC_3))
    fixtures.extend(run_tc_pipeline("test", TC_4))
    fixtures.extend(run_tc_pipeline("test", TC_5))

    engine = MatchingEngine()
    matches = engine.match_all(vessels, cargoes, fixtures)

    print("\n%s" % ("=" * 60))
    print("MATCHING: %d vessel(s), %d cargo(es), %d tc fixture(s) = %d match(es)" % (
        len(vessels), len(cargoes), len(fixtures), len(matches)))

    if matches:
        print("\n  Top 10 matches:")
        print()
        for i, m in enumerate(matches[:10]):
            print("  %2d. %-50s score=%5.1f" % (i + 1, m.label, m.score))
            print("      %s  |  %s -> %s" % (m.details, m.source_type, m.target_type))
    else:
        print("  ** NO MATCHES FOUND")
