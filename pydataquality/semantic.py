"""
Work out what a column *is* (an ID, an email, a date, a category...) before
judging it. Most false alarms in data checks come from applying a numeric or
categorical test to a column it does not suit, such as outlier detection on IDs.
"""

import re
from typing import Dict, List, Optional, Tuple

import pandas as pd

# Column kinds
ID = "id"
EMAIL = "email"
DATE = "date"
NUMBER = "number"
NUMBER_AS_TEXT = "number_as_text"
BOOLEAN = "boolean"
CATEGORY = "category"
TEXT = "text"
EMPTY = "empty"

SAMPLE_SIZE = 5000

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s.]+$")

_TIME = r"([ T]\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?\s*([AaPp][Mm])?(Z|[+-]\d{2}:?\d{2})?)?"
DATE_SHAPES: List[Tuple[str, "re.Pattern"]] = [
    ("2024-01-31", re.compile(r"^\d{4}-\d{1,2}-\d{1,2}" + _TIME + "$")),
    ("2024/01/31", re.compile(r"^\d{4}/\d{1,2}/\d{1,2}" + _TIME + "$")),
    ("31/01/2024", re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4}" + _TIME + "$")),
    ("31-01-2024", re.compile(r"^\d{1,2}-\d{1,2}-\d{4}" + _TIME + "$")),
    ("31.01.2024", re.compile(r"^\d{1,2}\.\d{1,2}\.\d{2,4}" + _TIME + "$")),
    ("31 Jan 2024", re.compile(r"^\d{1,2}[ -][A-Za-z]{3,9}[ ,-]+\d{2,4}" + _TIME + "$")),
    ("Jan 31, 2024", re.compile(r"^[A-Za-z]{3,9}\.? \d{1,2},? \d{4}" + _TIME + "$")),
]

_NUMBER_JUNK = re.compile(r"[,\s$€£₦%]")

ID_TOKENS = {"id", "uuid", "guid", "key"}
PAST_DATE_TOKENS = {
    "created", "updated", "modified", "birth", "dob", "born", "signup", "signed",
    "registered", "registration", "joined", "order", "ordered", "purchase",
    "purchased", "transaction", "paid", "payment", "invoice", "hire", "hired",
    "logged", "posted", "admission", "admitted", "timestamp", "received", "sold",
    "visit", "collected", "recorded", "submitted", "shipped",
}
FUTURE_DATE_TOKENS = {
    "due", "expiry", "expires", "expiration", "expire", "end", "deadline",
    "scheduled", "schedule", "delivery", "renewal", "renew", "valid", "maturity",
    "next", "until", "planned", "plan", "target", "forecast", "appointment",
    "departure", "arrival", "checkout", "checkin", "event", "start", "eta",
    "estimated", "expected",
}
NON_NEGATIVE_TOKENS = {
    "price", "qty", "quantity", "count", "salary", "weight", "height",
    "duration", "distance", "age", "population", "stock", "units",
}
PERCENT_TOKENS = {"percent", "percentage", "pct"}


def name_tokens(name) -> set:
    """Split a column name into lowercase words: 'OrderID' -> {'order', 'id'}."""
    text = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", str(name))
    text = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", text)
    return {t for t in re.split(r"[^A-Za-z0-9]+", text.lower()) if t}


def _sample(series: pd.Series) -> pd.Series:
    if len(series) > SAMPLE_SIZE:
        return series.sample(SAMPLE_SIZE, random_state=0)
    return series


def as_text(series: pd.Series) -> pd.Series:
    """Non-missing values as stripped strings, keeping the original index."""
    return series.dropna().astype(str).str.strip()


def date_shape(value: str) -> Optional[str]:
    """Name of the date layout a string follows, or None if it is not a date."""
    for label, pattern in DATE_SHAPES:
        if pattern.match(value):
            return label
    return None


def date_shapes(text: pd.Series) -> pd.Series:
    """Date layout per value (None where the value does not look like a date)."""
    return text.map(date_shape)


def parse_dates(text: pd.Series) -> pd.Series:
    """
    Parse text dates one layout at a time, so that a column mixing layouts is
    handled the same way on every pandas version.
    """
    shapes = date_shapes(text)
    parsed = pd.Series(pd.NaT, index=text.index, dtype="datetime64[ns]")
    for label in shapes.dropna().unique():
        group = text[shapes == label]
        dayfirst = label.startswith("31")
        values = pd.to_datetime(group, errors="coerce", dayfirst=dayfirst, utc=True)
        parsed.loc[group.index] = values.dt.tz_localize(None).astype("datetime64[ns]")
    return parsed


def to_number(text: pd.Series) -> pd.Series:
    """Parse numbers written as text ('1,200', '$45.50', '12%'). NaN if not a number."""
    cleaned = text.str.replace(_NUMBER_JUNK, "", regex=True)
    return pd.to_numeric(cleaned, errors="coerce")


def _looks_like_id(name, values: pd.Series) -> bool:
    if len(values) < 20:
        return bool(name_tokens(name) & ID_TOKENS) and values.is_unique
    unique_ratio = values.nunique() / len(values)
    if name_tokens(name) & ID_TOKENS:
        return unique_ratio >= 0.9
    if pd.api.types.is_integer_dtype(values) and values.is_unique:
        # 1, 2, 3, ... with no name hint: a row number
        return bool(values.is_monotonic_increasing) and str(name).lower() in (
            "unnamed: 0", "index", "row", "no", "sn", "s/n", "#",
        )
    return False


def infer_kind(series: pd.Series, name="") -> str:
    """Classify a column. See the module constants for the possible answers."""
    values = series.dropna()
    if len(values) == 0:
        return EMPTY
    if pd.api.types.is_bool_dtype(values):
        return BOOLEAN
    if pd.api.types.is_datetime64_any_dtype(values):
        return DATE
    if pd.api.types.is_numeric_dtype(values):
        return ID if _looks_like_id(name, values) else NUMBER

    text = values.astype(str).str.strip()
    text = text[text != ""]
    if len(text) == 0:
        return EMPTY
    sample = _sample(text)

    if sample.map(lambda v: bool(EMAIL_RE.match(v))).mean() >= 0.8:
        return EMAIL
    if date_shapes(sample).notna().mean() >= 0.8:
        return DATE
    if to_number(sample).notna().mean() >= 0.8:
        return NUMBER_AS_TEXT
    if set(sample.str.lower().unique()) <= {"true", "false", "yes", "no", "y", "n"}:
        return BOOLEAN

    unique_count = text.nunique()
    unique_ratio = unique_count / len(text)
    if name_tokens(name) & ID_TOKENS and unique_ratio >= 0.9:
        return ID
    if unique_count <= 50 or unique_ratio <= 0.05:
        return CATEGORY
    return TEXT


def infer_kinds(df: pd.DataFrame) -> Dict[str, str]:
    return {column: infer_kind(df[column], column) for column in df.columns}

