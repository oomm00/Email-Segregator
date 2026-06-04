import re

_BN = r'(?:\b|_)'

# words that are NEVER port names
_NON_PORT_WORDS = {
    "HATC", "BOX", "HATCH", "HATCHES", "GEAR", "CRANES", "CRANE",
    "GRABS", "DERRICK", "WINCH", "PUMP", "PUMPS", "TANK", "TANKS",
    "HOLD", "HOLDS", "DECK", "BULKHEADS", "CARGO", "GRAIN", "BALE",
    "SSW", "SCANTLING", "STRUCTURAL", "DRAFT", "TPC", "KNOTS", "KTS",
    "LSFO", "HSFO", "MGO", "MDO", "HFO", "IFO", "LADEN", "BALLAST",
    "CONS", "CONSUMPTION", "IDLE", "SPEED", "ABT", "ABOUT", "APPROX",
}

# ── vessel_name ──────────────────────────────────────────────
VESSEL_NAME = [
    re.compile(
        r'(?:M/V|MV|MOTOR\s+VESSEL)\s+["]?([A-Za-z0-9][A-Za-z0-9\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT|' + _BN + r'OPEN|' + _BN + r'ACCOUNT|' + _BN + r'LAY|' + _BN + r'LOAD|' + _BN + r'PORT|' + _BN + r'CANCEL|' + _BN + r'GRT|' + _BN + r'NRT))',
        re.I,
    ),
    re.compile(
        r'VESSEL\s*[:#=]\s*["]?([A-Za-z0-9][A-Za-z0-9\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT|' + _BN + r'OPEN|' + _BN + r'ACCOUNT))',
        re.I,
    ),
    re.compile(
        r'VSL\s*[:#=]\s*["]?([A-Za-z0-9][A-Za-z0-9\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT))',
        re.I,
    ),
    re.compile(
        r'(?:^|\n)\s*(?:\d+[\.\)]\s*)?(?:M/V|MV)\s+["]?([A-Z][A-Za-z0-9\s\-\.\'\"\(\)\/]+)["]?\s*$',
        re.M,
    ),
]

# ── account_name ─────────────────────────────────────────────
ACCOUNT_NAME = [
    re.compile(
        r'(?:ACCOUNT|ACCT|CHARTERER|OWNERS?)\s*[:#=]\s*["]?([A-Za-z0-9][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT|' + _BN + r'OPEN|' + _BN + r'VESSEL|' + _BN + r'MV))',
        re.I,
    ),
    re.compile(
        r'(?:ACCOUNT|ACCT|CHARTERER|OWNERS?)\s+["]?([A-Z][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)["]?\s*$',
        re.M,
    ),
]

# ── open_port ────────────────────────────────────────────────
OPEN_PORT = [
    re.compile(
        r'(?:OPEN\s+PORT|LOADPORT|LOADING\s+PORT|PORT\s+OF\s+LOADING|PLACE\s+OF\s+LOADING)\s*[:#=]\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT|' + _BN + r'OPEN|' + _BN + r'LAY|' + _BN + r'CANCEL|' + _BN + r'DATE|' + _BN + r'ACCOUNT))',
        re.I,
    ),
    re.compile(
        r'(?:LOAD|OPEN)\s+(?:PORT|DISCH)\s*[:#=]\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT))',
        re.I,
    ),
    re.compile(
        r'(?:AT|IN)\s+PORT\s+OF\s+["]?([A-Za-z][A-Za-z\s\-]+?)["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
        re.I,
    ),
    # inline: "OPEN XIAMEN, CHINA O/A ..." — with non-port word filter
    re.compile(
        r'OPEN\s+["]?(?!' + '|'.join(_NON_PORT_WORDS) + r'\b)([A-Z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|' + _BN + r'O/A|' + _BN + r'O\/A))',
        re.I,
    ),
    # "OPEN 25 MAY GABES, TUNISIA" — date before port after OPEN
    re.compile(
        r'OPEN\s+\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
        re.I,
    ),
]

# ── open_date (laycan) ────────────────────────────────────────
OPEN_DATE = [
    re.compile(
        r'(?:LAY(?:DOWN|CAN|ING)|OPEN\s+DATE|CANCEL|CANCELING|LAYDAYS|DELIVERY)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4}(?:\s*[-–]\s*\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4})?)["]?',
        re.I,
    ),
    re.compile(
        r'(?:LAY(?:DOWN|CAN|ING)|OPEN\s+DATE|CANCEL|CANCELING|LAYDAYS|DELIVERY)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        r'(?:LAY(?:DOWN|CAN|ING)|OPEN\s+DATE|CANCEL|CANCELING|LAYDAYS|DELIVERY|O/A|O\/A)\s*[:#=]?\s*'
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    # standalone ordinal date
    re.compile(
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
    ),
    # standalone date range
    re.compile(
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
    ),
    # year-less date range: "08-12 JUNE"
    re.compile(
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+)["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
    ),
    # O/A date range: "O/A 24-25 MAY 2026"
    re.compile(
        r'(?:O/A|O\/A)\s*["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    # O/A ordinal: "O/A 2ND JUNE 2026"
    re.compile(
        r'(?:O/A|O\/A)\s*["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
]

# ── vessel_type ──────────────────────────────────────────────
VESSEL_TYPE = [
    re.compile(
        r'(?:TYPE|VESSEL\s+TYPE|CLASS|DESCRIPTION)\s*[:#=]\s*["]?([A-Za-z][A-Za-z\s\-]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'DWT|' + _BN + r'GRT|' + _BN + r'NRT|' + _BN + r'OPEN|' + _BN + r'ACCOUNT|' + _BN + r'LAY|' + _BN + r'CANCEL))',
        re.I,
    ),
    re.compile(
        r'\b(BULK\s+CARRIER|TANKER|CONTAINER\s*(?:SHIP|VESSEL)?|GENERAL\s+CARGO|CHEMICAL\s+TANKER|PRODUCT\s+TANKER|LPG|LNG|VLCC|SUEZMAX|AFRAMAX|PANAMAX|CAPESIZE|HANDYSIZE|SUPRAMAX|ULTRAMAX)\b',
        re.I,
    ),
]

# ── vessel_size_dwt ──────────────────────────────────────────
VESSEL_SIZE_DWT = [
    re.compile(
        r'(?:DWT|DEADWEIGHT|SIZE)\s*[:#=]?\s*["]?(\d[\d,\.]*)\s*(?:DWT|MT|TONS?|TONNES?)?["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'OPEN|' + _BN + r'ACCOUNT|' + _BN + r'LAY|' + _BN + r'GRT|' + _BN + r'NRT|' + _BN + r'BUILT))',
        re.I,
    ),
    re.compile(
        r'(\d[\d,\.]*)\s*(?:DWT|DEADWEIGHT|D\.W\.T\.)',
        re.I,
    ),
    # "93K" format
    re.compile(
        r'(\d+)\s*K\s*(?:DWT|MT)?["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/))',
        re.I,
    ),
]

# ── date post-processing ─────────────────────────────────────
MONTH_NAMES = r"(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)"

SPLIT_DATE_RANGE = re.compile(
    r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+' + MONTH_NAMES + r'\s+(\d{4})',
    re.I,
)

KNOWN_VESSEL_TYPES = {
    "bulk carrier", "tanker", "container", "container ship", "container vessel",
    "general cargo", "chemical tanker", "product tanker", "crude oil tanker",
    "lpg", "lng", "vlcc", "suezmax", "aframax", "panamax", "capesize",
    "handysize", "supramax", "ultramax", "heavy lift", "ro-ro", "roro",
    "reefer", "offshore supply", "psv", "ahv", "drillship", "fps o",
    "bitumen carrier", "cement carrier", "wood chip carrier",
}
