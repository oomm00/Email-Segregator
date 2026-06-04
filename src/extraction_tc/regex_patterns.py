import re

_BN = r'(?:\b|_)'  # word boundary helper

# ── account_name ─────────────────────────────────────────────
ACCOUNT_NAME = [
    re.compile(
        r'(?:A/C|ACCOUNT|ACC\b|ACCT|CHARTERER|OWNERS?)\s*[:#=]?\s*["]?([A-Za-z0-9][A-Za-z0-9\s\-\.&\'\"\(\)\,]+?)(?=\s*(?:,|\n|\r|$|\/|' + _BN + r'VESSEL|' + _BN + r'MV|' + _BN + r'DELIVERY|' + _BN + r'LAY|' + _BN + r'LC\b|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'DWT))',
        re.I,
    ),
]

# ── vessel_name ──────────────────────────────────────────────
VESSEL_NAME = [
    re.compile(
        r'(?:M/V|MV)\s+["]?([A-Za-z0-9][A-Za-z0-9\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT|' + _BN + r'OPEN|' + _BN + r'DELIVERY|' + _BN + r'LAY|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'ACCOUNT))',
        re.I,
    ),
    re.compile(
        r'VESSEL\s*[:#=]\s*["]?([A-Z][A-Za-z0-9\s\-\.\'\"\(\)\/]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'DWT|' + _BN + r'OPEN|' + _BN + r'DELIVERY|' + _BN + r'LAY|' + _BN + r'REDEL|' + _BN + r'PERIOD))',
        re.I,
    ),
]

# ── delivery_port ────────────────────────────────────────────
_DELIVERY_LABEL = r'(?:DELIVER(?:Y|ED)|DELY\b)'
DELIVERY_PORT = [
    re.compile(
        r'(?:' + _DELIVERY_LABEL + r'\s+(?:PORT|PLACE|AT|IN|POSITION|SPOT))\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/' + _BN + r'LAY|' + _BN + r'LC\b|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'ACCOUNT))',
        re.I,
    ),
    re.compile(
        r'' + _DELIVERY_LABEL + r'\s*[:#=]\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/' + _BN + r'LAY|' + _BN + r'LC\b|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'ACCOUNT))',
        re.I,
    ),
    re.compile(
        r'(?:BASIS\s+' + _DELIVERY_LABEL + r'\s+(?:AT|IN|PORT\s+OF)?|' + _DELIVERY_LABEL + r'\s+(?:AT|IN|PORT\s+OF)?)\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
        re.I,
    ),
]

# ── delivery_date (laycan) ────────────────────────────────────
_DD_LABEL = r'(?:LC\b|LAY(?:DOWN|CAN|ING|\/CAN)?|DELIVER(?:Y|ED)\s+DATE|DELY\b|CANCEL(?:LING)?|PWWD|LAYDATE)'
DELIVERY_DATE = [
    re.compile(
        _DD_LABEL + r'\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4}(?:\s*[-–]\s*\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4})?)["]?',
        re.I,
    ),
    re.compile(
        _DD_LABEL + r'\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        _DD_LABEL + r'\s*[:#=]?\s*'
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        _DD_LABEL + r'\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+)["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'COM|' + _BN + r'DWT))',
        re.I,
    ),
    re.compile(
        r'(?:BASIS\s+DELIVERY\s+)(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})',
        re.I,
    ),
    re.compile(
        r'(?:DELIVERY|DELIVER(?:Y|ED)|DELY\b)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        r'(?:DELIVERY|DELIVER(?:Y|ED)|DELY\b)\s*[:#=]?\s*'
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    # Standalone ordinal/date range without year
    re.compile(
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+)["]?(?=\s*(?:,|\n|\r|\.(?!\w)|' + _BN + r'1\s+TCT|$|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'COM|' + _BN + r'DWT))',
        re.I,
    ),
    # Standalone ordinal date without year
    re.compile(
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+)["]?(?=\s*(?:,|\n|\r|\.(?!\w)|' + _BN + r'1\s+TCT|$|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'COM))',
        re.I,
    ),
    # Month qualifier (FULL MAY, MID JULY, etc.)
    re.compile(
        r'["]?((?:FULL|MID|EARLY|LATE)\s+(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?))["]?(?=\s*(?:,|\n|\r|\.(?!\w)|' + _BN + r'1\s+TCT|$))',
        re.I,
    ),
]

# ── redelivery_port ─────────────────────────────────────────
REDELIVERY_PORT = [
    re.compile(
        r'(?:REDELIVER(?:Y|ED)\s+(?:PORT|PLACE|AT|IN|POSITION|SPOT)|REDEL\s+PORT|ROP)\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'ACCOUNT))',
        re.I,
    ),
    re.compile(
        r'REDELIVERY\s*[:#=]\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'ACCOUNT))',
        re.I,
    ),
    re.compile(
        r'(?:REDELIVERY|REDEL)\s*(?:AT|IN|PORT\s+OF)?\s*[:#=]?\s*["]?([A-Za-z][A-Za-z\s\-\.\'\"\(\)]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$))',
        re.I,
    ),
]

# ── redelivery_date ─────────────────────────────────────────
REDELIVERY_DATE = [
    re.compile(
        r'(?:REDELIVER(?:Y|ED)\s+DATE|REDEL\s+DATE)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4}(?:\s*[-–]\s*\d{1,2}\s*[\/\-\.]\s*\d{1,2}\s*[\/\-\.]\s*\d{2,4})?)["]?',
        re.I,
    ),
    re.compile(
        r'(?:REDELIVER(?:Y|ED)\s+DATE|REDEL\s+DATE)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        r'(?:REDELIVER(?:Y|ED)\s+DATE|REDEL\s+DATE)\s*[:#=]?\s*'
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        r'(?:REDEL|REDELIVERY)\s*[:#=]?\s*'
        r'["]?(\d{1,2}\s*[-–]\s*\d{1,2}\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
    re.compile(
        r'(?:REDEL|REDELIVERY)\s*[:#=]?\s*'
        r'["]?(\d{1,2}(?:st|nd|rd|th)?\s+[A-Za-z]+\s+\d{4})["]?',
        re.I,
    ),
]

# ── charter_period ───────────────────────────────────────────
_CHARTER_LABEL = r'(?:PERIOD|DURATION|TC\s+PERIOD|TIME\s+CHARTER\s+PERIOD|CHARTER\s+PERIOD)'
_CHARTER_UNIT = r'(?:MONTHS?|MOS?|YRS?|YEARS?|DAYS?|WEEKS?)'
_CHARTER_TERM = r'(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'DELIVERY|' + _BN + r'REDEL|' + _BN + r'HIRE|' + _BN + r'WOG\b)'
CHARTER_PERIOD = [
    # Labeled + value + unit (plain — no ABOUT prefix)
    re.compile(
        _CHARTER_LABEL + r'\s*[:#=]?\s*'
        r'["]?([\d\s\-\.\/]+?\s*(?:' + _CHARTER_UNIT + r'))["]?(?=\s*' + _CHARTER_TERM + r')',
        re.I,
    ),
    # Labeled + ABOUT/APPROX/ABT + value + unit
    re.compile(
        _CHARTER_LABEL + r'\s*[:#=]?\s*(?:ABOUT|APPROX|APPROXIMATELY|ABT)\s+'
        r'["]?([\d\s\-\.\/]+?\s*(?:' + _CHARTER_UNIT + r'))["]?(?=\s*' + _CHARTER_TERM + r')',
        re.I,
    ),
    # Unlabeled value + unit + TC
    re.compile(
        r'["]?([\d\s\-\.\/]+?\s*(?:MONTHS?|MOS?|YRS?|YEARS?|DAYS?))\s*(?:TC|TIME\s+CHARTER)',
        re.I,
    ),
    # ABOUT/APPROX/ABT + value + unit
    re.compile(
        r'(?:ABOUT|APPROX|APPROXIMATELY|ABT)\s+["]?([\d\s\-\.\/]+?\s*(?:' + _CHARTER_UNIT + r'))["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'WOG\b))',
        re.I,
    ),
    # Standalone value + unit (for ranges like "1-3 YEARS")
    re.compile(
        r'["]?([\d\s\-\.\/]+?\s*(?:' + _CHARTER_UNIT + r'))["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TRY\b|' + _BN + r'FLAT\b|' + _BN + r'INDEX\b|' + _BN + r'WOG\b))',
        re.I,
    ),
]

# ── hire_rate ────────────────────────────────────────────────
HIRE_RATE = [
    re.compile(
        r'(?:HIRE|HIRE\s+RATE|DAILY\s+HIRE|RATE)\s*[:#=]?\s*["]?\$?(\d[\d,\.]*)\s*(?:USD|PER\s+DAY|D?AILY)?["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/' + _BN + r'COM|' + _BN + r'PERIOD|' + _BN + r'DELIVERY|' + _BN + r'REDEL))',
        re.I,
    ),
    re.compile(
        r'\$(\d[\d,\.]*)\s*(?:PER\s+DAY|DAILY|D?AILY)',
        re.I,
    ),
]

# ── commission_pct ───────────────────────────────────────────
COMMISSION = [
    re.compile(
        r'(?:COM(?:M(?:ISSION)?)?|TTL|TOTAL\s+COM|BROKERAGE)\s*[:#=]?\s*["]?(\d[\d,\.]*)\s*%?["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/' + _BN + r'ACCOUNT|' + _BN + r'VESSEL|' + _BN + r'HIRE|' + _BN + r'PERIOD))',
        re.I,
    ),
    re.compile(
        r'["]?(\d[\d,\.]*)\s*(?:%|PCT)?\s*(?:ADDCOM|ADDOM|ADCOM|ADDCOMM|ADC)\b',
        re.I,
    ),
    re.compile(
        r'(\d[\d,\.]*)\s*%\s*(?:COM(?:M(?:ISSION)?)?|BROKERAGE|TTL|ADC|ADDCOM|ADDOM)',
        re.I,
    ),
]

# ── intended_cargo ───────────────────────────────────────────
INTENDED_CARGO = [
    re.compile(
        r'(?:INTEND(?:ED)?\s+CARGO)\s*[:#=]?\s*["]?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)\/]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|' + _BN + r'ACCOUNT|' + _BN + r'VESSEL|' + _BN + r'DELIVERY|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE))',
        re.I,
    ),
    re.compile(
        r'(?:CARGO|COMMODITY|TRADE)\s*[:#=]?\s*["]?([A-Z][A-Za-z0-9\s\-\.\'\"\(\)\/]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|' + _BN + r'ACCOUNT|' + _BN + r'VESSEL|' + _BN + r'DELIVERY|' + _BN + r'REDEL|' + _BN + r'PERIOD|' + _BN + r'HIRE))',
        re.I,
    ),
    re.compile(
        r'(?:1\s+TCT|TCT)\s+WITH\s+["\']?([A-Za-z][A-Za-z0-9\s\-\.\'\"\(\)\/]+?)(?=\s*(?:,|\n|\r|\.(?!\w)|$|' + _BN + r'REDEL|' + _BN + r'DELIVERY|' + _BN + r'DURATION|' + _BN + r'PERIOD|' + _BN + r'HIRE|' + _BN + r'COM|' + _BN + r'DWT|' + _BN + r'LAY|' + _BN + r'LC\b|' + _BN + r'LOAD))',
        re.I,
    ),
]

# ── vessel_dwt ────────────────────────────────────────────────
VESSEL_DWT = [
    re.compile(
        r'(?:DWT|DEADWEIGHT)\s*[:#=]?\s*["]?(\d[\d,\.]*)\s*(?:DWT|MT|TONS?|TONNES?)?["]?(?=\s*(?:,|\n|\r|\.(?!\w)|$|\/|' + _BN + r'TYPE|' + _BN + r'OPEN|' + _BN + r'DELIVERY|' + _BN + r'REDEL|' + _BN + r'HIRE|' + _BN + r'PERIOD))',
        re.I,
    ),
    re.compile(
        r'(\d[\d,\.]*)\s*K?\s*(?:DWT|DEADWEIGHT|D\.W\.T\.)',
        re.I,
    ),
    re.compile(
        r'(?:DEADWEIGHT|DWT)\s+["]?(\d[\d,\.]*)',
        re.I,
    ),
]

# ── date post-processing ─────────────────────────────────────
MONTH_NAMES = r"(?:JAN(?:UARY)?|FEB(?:RUARY)?|MAR(?:CH)?|APR(?:IL)?|MAY|JUN(?:E)?|JUL(?:Y)?|AUG(?:UST)?|SEP(?:TEMBER)?|OCT(?:OBER)?|NOV(?:EMBER)?|DEC(?:EMBER)?)"

SPLIT_DATE_RANGE = re.compile(
    r'(\d{1,2})\s*[-–]\s*(\d{1,2})\s+' + MONTH_NAMES + r'\s+(\d{4})',
    re.I,
)
