import re

# ── account_name ─────────────────────────────────────────────
ACCOUNT_NAME = [
    re.compile(
        r'(?:ACCOUNT|ACCT|CHARTERER|OWNERS?)\s*[:#=]\s*["]?([A-Za-z0-9][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|CARGO|COMMODITY|PRODUCT|TYPE|QTY|QUANTITY|LOAD|DISCH|PORT|POL|POD|LP|DP|LAYCAN|PWWD|COM|COMM))',
        re.I,
    ),
    re.compile(
        r'(?:ACCOUNT|ACCT|CHARTERER|OWNERS?)\s+["]?([A-Z][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)["]?\s*$',
        re.M,
    ),
]

# ── cargo_name ────────────────────────────────────────────────
CARGO_NAME = [
    re.compile(
        r'(?:CARGO|COMMODITY|PRODUCT)\s*[:#=]?\s*["]?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|TYPE|QTY|QUANTITY|LOAD|DISCH|PORT|POL|POD|LP|DP|LAYCAN|COM|COMM))',
        re.I,
    ),
    re.compile(
        r'(?:CARGO|COMMODITY|PRODUCT)\s+["]?([A-Z][A-Za-z0-9\s\-\.\'\"\(\)]+?)["]?\s*$',
        re.M,
    ),
    # "Cargo:30,000 mts of Urea in bulk" — labeled prefix + qty of/in cargo
    re.compile(
        r'(?:CARGO|COMMODITY|PRODUCT)\s*[:#=]?\s*\d[\d,\.]*(?:\s+\d{3})?\s*(?:MTS?|KMT|TONS?|TONNES?)\s*(?:OF|IN)\s+["\']?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)]+?)["\']?(?=\s*(?:,|\n|\r|$))',
        re.I,
    ),
    # unlabeled after quantity: "15,000 - 20,000 MTS 10PCT MOLOCHOPT" or "20 000 mt HRC"
    re.compile(
        r'\d[\d,\.]*(?:\s+\d{3})?\s*(?:[-–]\s*\d[\d,\.]*)?\s*(?:MTS?|KMT|TONS?|TONNES?)\s*(?:\d+PCT\s+)?["\']?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)]+?)["\']?(?=\s*(?:\n|\r|$))',
        re.I,
    ),
]

# ── loading_port ──────────────────────────────────────────────
LOADING_PORT = [
    re.compile(
        r'(?:LOAD\s+PORT|POL|LP|PORT\s+OF\s+LOADING|LOADING\s+PORT|PLACE\s+OF\s+LOADING)\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)\+]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|DISCHARGE|UNLOAD|DEST|POD|DP|LAYCAN|CARGO|ACCOUNT|TYPE|QTY|COM))',
        re.I,
    ),
    re.compile(
        r'(?:LOADING?|FROM)\s+(?:AT|IN|PORT\s+OF)?\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)\+]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
        re.I,
    ),
]

# ── discharge_port ────────────────────────────────────────────
DISCHARGE_PORT = [
    re.compile(
        r'(?:DISCHARGE\s+PORT|DESTINATION|DEST|POD|DP|PORT\s+OF\s+DISCHARGE|DISCH\s+PORT|UNLOAD\s+PORT)\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)\+]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|LOAD|POL|LP|LAYCAN|CARGO|ACCOUNT|TYPE|QTY|COM))',
        re.I,
    ),
    re.compile(
        r'(?:DISCH|DISCHARGE|UNLOAD|TO)\s+(?:AT|IN|PORT\s+OF)?\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)\+]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
        re.I,
    ),
]

# ── laycan ────────────────────────────────────────────────────
_WS = r'[ \t]*'
LAYCAN = [
    re.compile(
        r'(?:LAY(?:DOWN|CAN|ING)|PWWD|CANCEL|CANCELING|DELIVERY|LAYDATE)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4}(?:\s*[-–]\s*\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4})?)["]?',
        re.I,
    ),
    re.compile(
        r'(?:LAY(?:DOWN|CAN|ING)|PWWD|CANCEL|CANCELING|DELIVERY|LAYDATE)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        r'(?:LAY(?:DOWN|CAN|ING)|PWWD|CANCEL|CANCELING)\s*[:#=]?\s*'
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?(?=' + _WS + r'(?:,|\n|\r|$))',
    ),
    re.compile(
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?(?=' + _WS + r'(?:,|\n|\r|$))',
    ),
    re.compile(
        r'["]?((?:MID|FULL)\s+[A-Za-z]+\s+\d{4})["]?(?=' + _WS + r'(?:,|\n|\r|$))',
    ),
    re.compile(
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+)["]?(?=' + _WS + r'(?:,|\n|\r|$))',
    ),
    re.compile(
        r'["]?(\d{1,2}\s+[A-Za-z]+\s+[-–]\s+\d{1,2}\s+[A-Za-z]+)["]?(?=' + _WS + r'(?:,|\n|\r|$))',
    ),
]

# ── cargo_type ────────────────────────────────────────────────
CARGO_TYPE = [
    re.compile(
        r'(?:CARGO\s+TYPE|TYPE|CLASS|DESCRIPTION)\s*[:#=]\s*["]?([A-Za-z][A-Za-z\s\-]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|QTY|QUANTITY|DWT|LOAD|DISCH|PORT|COM|COMM))',
        re.I,
    ),
]

# ── quantity ──────────────────────────────────────────────────
QUANTITY = [
    re.compile(
        r'(?:QUANTITY|QTY|TOTAL\s+QUANTITY|TOTAL\s+QTY|MIN\s*\/\s*MAX|CARGO\s+QUANTITY)\s*[:#=]?\s*'
        r'["]?(\d[\d,\.]*)\s*(?:[-–\/]\s*(\d[\d,\.]*))?\s*(?:MT|KMT|TONS?|TONNES?)?["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|LOAD|DISCH|PORT|POL|LAYCAN|TYPE|COM))',
        re.I,
    ),
    # unlabeled quantity at line start: "15,000 - 20,000 MTS" or "20 000 mt"
    re.compile(
        r'(?:^|\n)\s*["]?(\d[\d,\.]+)(?:\s+(\d{3}))?\s*(?:[-–\/]\s*(\d[\d,\.]+))?\s*(?:MTS?|KMT|TONS?|TONNES?)',
        re.I | re.M,
    ),
    # generic quantity
    re.compile(
        r'(\d[\d,\.]*)\s*(?:[-–\/]\s*(\d[\d,\.]*))?\s*x?\s*(?:\d[\d,\.]*\s*)?(?:MT|KMT|METRIC\s+TONS?)',
        re.I,
    ),
]

# ── commission ────────────────────────────────────────────────
COMMISSION = [
    re.compile(
        r'(?:COM(?:M(?:ISSION)?)?|BROKERAGE|TTL|TOTAL\s+COM)\s*[:#=]?\s*["]?(\d[\d,\.]*)\s*%?\s*(?:ADDCOM|ADDOM|PCT|TTL|HERE)?["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|\s*ACCOUNT|\s*CARGO|\s*TYPE|\s*LOAD|\s*DISCH|\s*PORT|\s*LAYCAN|\s*PCT|\s*TTL|\s*TOTAL))',
        re.I,
    ),
    re.compile(
        r'(\d[\d,\.]*)\s*%\s*(?:COM(?:M(?:ISSION)?)?|BROKERAGE|TTL|PCT)',
        re.I,
    ),
    re.compile(
        r'(\d[\d,\.]*)\s*(?:PCT|%)\s*(?:ADDCOM|ADDOM)\b',
        re.I,
    ),
]

# ── load_rate / discharge_rate ───────────────────────────────
LOAD_RATE = [
    re.compile(
        r'(?:LOAD(?:ING)?\s+(?:RATE|RATE\s+PER\s+[A-Z]+)|LOADRATE)\s*[:#=]?\s*["]?(\d[\d,\.]+)\s*(?:MT|KMT|TONS?)?\s*(?:\/|PER\s+[A-Z]+\s*)?(?:PWWD\s+SSHEX|PWWD\s+SHEX|SSHEX|SHINC|SHEX|PWWD)?["]?(?=\s*(?:\n|\r|\.(?!\w)|$|\/|DISCH|PORT|COM|COMM))',
        re.I,
    ),
    re.compile(
        r'(?:LOAD(?:ING)?\s+(?:RATE|RATE\s+PER\s+[A-Z]+)|LOADRATE)\s*[:#=]?\s*["]?(\d[\d,\.]+)',
        re.I,
    ),
    re.compile(
        r'(?:FIOS\w*\s+)?["]?(\d{3,6})\s*(?:MT|KMT|TONS?)?\s*(?:FHINC|SHEX|SSHEX|SHINC|PWWD)?["]?(?=\s*(?:\n|\r|$|\/|CQD))',
        re.I,
    ),
]

DISCHARGE_RATE = [
    re.compile(
        r'(?:DISCH(?:ARGE)?\s+(?:RATE|RATE\s+PER\s+[A-Z]+)|DISCHRATE|UNLOAD(?:ING)?\s+RATE)\s*[:#=]?\s*["]?(\d[\d,\.]+)\s*(?:MT|KMT|TONS?)?\s*(?:\/|PER\s+[A-Z]+\s*)?(?:PWWD\s+SSHEX|PWWD\s+SHEX|SSHEX|SHINC|SHEX|PWWD)?["]?(?=\s*(?:\n|\r|\.(?!\w)|$|\/|LOAD|PORT|COM|COMM))',
        re.I,
    ),
    re.compile(
        r'(?:DISCH(?:ARGE)?\s+(?:RATE|RATE\s+PER\s+[A-Z]+)|DISCHRATE|UNLOAD(?:ING)?\s+RATE)\s*[:#=]?\s*["]?(\d[\d,\.]+)',
        re.I,
    ),
    re.compile(
        r'["]?(CQD)\s*(?:DISCH|DISC|DISCHARGE)?["]?(?=\s*(?:\n|\r|$))',
        re.I,
    ),
]

# ── known cargo types for validation ─────────────────────────
KNOWN_CARGO_TYPES = {
    "iron ore", "bauxite", "alumina", "coal", "coking coal", "thermal coal",
    "crude oil", "fuel oil", "gas oil", "diesel", "gasoline", "jet fuel",
    "naphtha", "lpg", "lng", "soybeans", "soybean meal", "corn", "wheat",
    "barley", "rice", "sugar", "fertilizer", "phosphate", "potash",
    "urea", "containers", "steel", "steel products", "scrap", "cement",
    "clinker", "limestone", "gypsum", "bauxite", "manganese ore",
    "copper concentrate", "zinc concentrate", "lead concentrate",
    "nickel ore", "chrome ore", "ilmenite", "rutile", "zircon",
    "pet coke", "coke", "wood pellets", "wood chips", "logs",
    "palm oil", "vegetable oil", "molasses", "ethanol",
    "general cargo", "project cargo", "break bulk",
}

# ── date post-processing ─────────────────────────────────────
MONTH_NAMES = r"(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)"

SPLIT_DATE_RANGE = re.compile(
    r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+' + MONTH_NAMES + r'\s+(\d{4})',
    re.I,
)

# ── quantity post-processing ─────────────────────────────────
SPLIT_QTY_RANGE = re.compile(
    r'(\d[\d,\.]*)\s*[-–\/]\s*(\d[\d,\.]*)',
)
