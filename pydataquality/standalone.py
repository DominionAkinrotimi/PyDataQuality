"""
Checks that need no history: things that are wrong in any file, and things
that are wrong given what a column is.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from . import semantic as sem

PROBLEM = "problem"
WARNING = "warning"
NOTE = "note"
LEVEL_ORDER = {PROBLEM: 0, WARNING: 1, NOTE: 2}

ALL_COLUMNS = "(whole file)"


@dataclass
class Finding:
    """One thing a reader should know about the file, in plain language."""

    level: str  # 'problem', 'warning' or 'note'
    code: str  # short stable name, e.g. 'duplicates'
    column: str
    message: str
    count: int = 0
    examples: List = field(default_factory=list)
    rows: Optional[pd.Index] = None  # index labels of the affected rows
    why: str = ""  # how the tool decided, shown on request

    @property
    def key(self) -> str:
        return f"{self.code}:{self.column}"

    def to_dict(self) -> Dict:
        return {
            "level": self.level,
            "code": self.code,
            "column": self.column,
            "message": self.message,
            "count": int(self.count),
            "examples": [str(e) for e in self.examples],
            "why": self.why,
        }


def n(count, singular, plural=None) -> str:
    """'1 row' / '1,200 rows'."""
    word = singular if count == 1 else (plural or singular + "s")
    return f"{count:,} {word}"


def num(value) -> str:
    """A number for a sentence: 1989 stays 1989, 1200000 becomes 1,200,000."""
    value = float(value)
    return f"{value:.6g}" if abs(value) < 10000 else f"{value:,.6g}"


def show(values, limit=3) -> str:
    """Quote a few example values for a message."""
    seen = []
    for value in values:
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        text = str(value)
        if len(text) > 40:
            text = text[:37] + "..."
        if text not in seen:
            seen.append(text)
        if len(seen) == limit:
            break
    return ", ".join(f'"{v}"' for v in seen)


def duplicate_mask(df: pd.DataFrame) -> pd.Series:
    try:
        return df.duplicated()
    except TypeError:  # unhashable cells such as lists
        return df.astype(str).duplicated()


def check_structure(df: pd.DataFrame, kinds: Dict[str, str]) -> List[Finding]:
    findings = []
    if len(df) == 0:
        return [Finding(PROBLEM, "no_rows", ALL_COLUMNS, "The file has no rows.")]

    unnamed = [c for c in df.columns if str(c).startswith("Unnamed:")]
    if unnamed:
        findings.append(
            Finding(
                WARNING, "no_header", ALL_COLUMNS,
                f"{n(len(unnamed), 'column')} {'has' if len(unnamed) == 1 else 'have'} no header. "
                "The first row may not be the header row.",
                count=len(unnamed),
            )
        )

    duplicates = duplicate_mask(df)
    count = int(duplicates.sum())
    if count:
        # With an identifier column a repeated row is certainly a mistake. Without
        # one, two people can honestly share every value, so a few repeats in a
        # narrow table are only worth a note.
        if sem.ID in kinds.values():
            level = PROBLEM
        elif count / len(df) >= 0.01 and len(df.columns) >= 5:
            level = WARNING
        else:
            level = NOTE
        findings.append(
            Finding(
                level, "duplicates", ALL_COLUMNS,
                f"{n(count, 'row is an exact copy', 'rows are exact copies')} of another row.",
                count=count, rows=df.index[duplicates],
                why="Every column in these rows matches an earlier row.",
            )
        )

    empty = [c for c, kind in kinds.items() if kind == sem.EMPTY]
    for column in empty:
        findings.append(
            Finding(WARNING, "empty_column", str(column), f"{column} is completely empty.", count=len(df))
        )
    return findings


def check_missing(df: pd.DataFrame, column, kind: str) -> List[Finding]:
    if kind == sem.EMPTY:
        return []
    missing = df[column].isna()
    count = int(missing.sum())
    share = count / len(df)
    if share < 0.05:
        return []
    level = WARNING if share >= 0.5 else NOTE
    return [
        Finding(
            level, "missing", str(column),
            f"{column} is empty in {n(count, 'row')} ({share:.0%}).",
            count=count, rows=df.index[missing],
        )
    ]


def check_unique_id(df: pd.DataFrame, column, kind: str) -> List[Finding]:
    """An ID column that is almost, but not quite, unique."""
    if kind != sem.ID:
        return []
    distinct_rows = df[~duplicate_mask(df)]
    values = distinct_rows[column].dropna()
    repeated = values[values.duplicated(keep=False)]
    if repeated.empty:
        return []
    return [
        Finding(
            PROBLEM, "id_repeats", str(column),
            f"{column} should be unique, but {n(repeated.nunique(), 'value appears', 'values appear')} "
            f"more than once, e.g. {show(repeated.unique())}.",
            count=len(repeated), examples=list(repeated.unique()[:5]), rows=repeated.index,
            why="The column is named like an identifier and nearly every value is different. "
            "Exact duplicate rows are not counted here.",
        )
    ]


def check_spelling(df: pd.DataFrame, column, kind: str) -> List[Finding]:
    """The same value written with different capitals or spacing."""
    if kind not in (sem.CATEGORY, sem.TEXT):
        return []
    values = df[column].dropna().astype(str)
    counts = values.value_counts()
    if len(counts) > 5000:
        return []
    normalised = counts.index.to_series().str.strip().str.replace(r"\s+", " ", regex=True).str.casefold()
    groups = counts.groupby(normalised.values).agg(["size", "idxmax"])
    clashing = groups[groups["size"] > 1]
    if clashing.empty:
        return []

    spellings = normalised[normalised.isin(clashing.index)]
    main_spellings = set(clashing["idxmax"])
    minority = [value for value in spellings.index if value not in main_spellings]
    affected = values[values.isin(minority)]
    first = spellings[spellings == clashing.index[0]].index.tolist()
    more = f" ({n(len(clashing) - 1, 'more value')} like this)" if len(clashing) > 1 else ""
    return [
        Finding(
            WARNING, "spelling", str(column),
            f"{column} has {len(first)} spellings of the same value: {show(first, 4)}{more}. "
            f"{n(len(affected), 'row uses', 'rows use')} a less common spelling.",
            count=len(affected), examples=first[:5], rows=affected.index,
            why="Values are compared after removing extra spaces and ignoring capital letters.",
        )
    ]


def check_email(df: pd.DataFrame, column, kind: str) -> List[Finding]:
    if kind != sem.EMAIL:
        return []
    text = sem.as_text(df[column])
    bad = text[~text.map(lambda v: bool(sem.EMAIL_RE.match(v)))]
    if bad.empty:
        return []
    return [
        Finding(
            WARNING, "bad_email", str(column),
            f"{column} has {n(len(bad), 'value that is not an email address', 'values that are not email addresses')}, "
            f"e.g. {show(bad)}.",
            count=len(bad), examples=list(bad.unique()[:5]), rows=bad.index,
        )
    ]


def _future_level(column) -> Optional[str]:
    tokens = sem.name_tokens(column)
    if tokens & sem.FUTURE_DATE_TOKENS:
        return None  # due dates, expiry dates and the like are meant to be ahead
    return PROBLEM if tokens & sem.PAST_DATE_TOKENS else WARNING


def check_dates(df: pd.DataFrame, column, kind: str, today=None) -> List[Finding]:
    if kind != sem.DATE:
        return []
    findings = []
    series = df[column]
    today = pd.Timestamp(today) if today is not None else pd.Timestamp.now()

    if pd.api.types.is_datetime64_any_dtype(series):
        parsed = series.dropna()
        if getattr(parsed.dt, "tz", None) is not None:
            parsed = parsed.dt.tz_localize(None)
    else:
        text = sem.as_text(series)
        text = text[text != ""]
        shapes = sem.date_shapes(text)

        not_dates = text[shapes.isna()]
        if len(not_dates):
            findings.append(
                Finding(
                    WARNING, "bad_date", str(column),
                    f"{column} has {n(len(not_dates), 'value that is not a date', 'values that are not dates')}, "
                    f"e.g. {show(not_dates)}.",
                    count=len(not_dates), examples=list(not_dates.unique()[:5]), rows=not_dates.index,
                )
            )

        layout_counts = shapes.dropna().value_counts()
        if len(layout_counts) > 1:
            main = layout_counts.index[0]
            others = text[shapes.notna() & (shapes != main)]
            findings.append(
                Finding(
                    WARNING, "mixed_dates", str(column),
                    f"{column} mixes {len(layout_counts)} date formats. Most look like {main}, "
                    f"but {n(len(others), 'row looks', 'rows look')} like {show(others, 2)}.",
                    count=len(others), examples=list(others.unique()[:5]), rows=others.index,
                    why="Mixed formats are often read wrongly, for example 03/04 as March or April.",
                )
            )
        parsed = sem.parse_dates(text).dropna()

    level = _future_level(column)
    if level and len(parsed):
        future = parsed[parsed > today + pd.Timedelta(days=1)]
        if len(future):
            findings.append(
                Finding(
                    level, "future_date", str(column),
                    f"{column} has {n(len(future), 'date')} in the future "
                    f"(latest: {future.max().date()}).",
                    count=len(future), examples=[str(d.date()) for d in future.head(5)], rows=future.index,
                    why="Compared with today's date on this computer.",
                )
            )
    return findings


def check_number_text(df: pd.DataFrame, column, kind: str) -> List[Finding]:
    """A column of numbers that was read as text because a few values are not numbers."""
    if kind != sem.NUMBER_AS_TEXT:
        return []
    text = sem.as_text(df[column])
    text = text[text != ""]
    bad = text[sem.to_number(text).isna()]
    if bad.empty:
        return []
    return [
        Finding(
            WARNING, "not_a_number", str(column),
            f"{column} is mostly numbers, but {n(len(bad), 'value is', 'values are')} not: {show(bad)}.",
            count=len(bad), examples=list(bad.unique()[:5]), rows=bad.index,
            why="These values stop the column being treated as numbers in a sum or average.",
        )
    ]


def numeric_values(df: pd.DataFrame, column, kind: str) -> Optional[pd.Series]:
    if kind == sem.NUMBER:
        values = df[column].dropna()
        return None if pd.api.types.is_bool_dtype(values) else values
    if kind == sem.NUMBER_AS_TEXT:
        return sem.to_number(sem.as_text(df[column])).dropna()
    return None


def check_impossible(df: pd.DataFrame, column, kind: str) -> List[Finding]:
    """Values that cannot be right given what the column name says it holds."""
    values = numeric_values(df, column, kind)
    if values is None or values.empty:
        return []
    tokens = sem.name_tokens(column)
    findings = []

    if "age" in tokens:
        bad = values[(values < 0) | (values > 120)]
        if len(bad):
            findings.append(
                Finding(
                    PROBLEM, "impossible", str(column),
                    f"{column} has {n(len(bad), 'impossible value')}: {show(bad.unique())}. "
                    "An age should be between 0 and 120.",
                    count=len(bad), examples=list(bad.unique()[:5]), rows=bad.index,
                )
            )
    elif tokens & sem.PERCENT_TOKENS:
        bad = values[(values < 0) | (values > 100)]
        if len(bad):
            findings.append(
                Finding(
                    WARNING, "impossible", str(column),
                    f"{column} has {n(len(bad), 'value')} outside 0 to 100: {show(bad.unique())}.",
                    count=len(bad), examples=list(bad.unique()[:5]), rows=bad.index,
                )
            )
    elif tokens & sem.NON_NEGATIVE_TOKENS:
        bad = values[values < 0]
        if len(bad):
            findings.append(
                Finding(
                    WARNING, "negative", str(column),
                    f"{column} has {n(len(bad), 'negative value')}: {show(bad.unique())}.",
                    count=len(bad), examples=list(bad.unique()[:5]), rows=bad.index,
                )
            )
    return findings


def _spread_distance(values: pd.Series) -> Optional[pd.Series]:
    """How many interquartile ranges each value lies beyond the middle half."""
    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    iqr = q3 - q1
    if iqr == 0:
        return None
    below = (q1 - values).clip(lower=0)
    above = (values - q3).clip(lower=0)
    return (below + above) / iqr


def check_extremes(df: pd.DataFrame, column, kind: str, already=None) -> List[Finding]:
    """
    Values very far from the rest.

    Deliberately strict, because this is the check most likely to cry wolf.
    A value counts only if it is more than 3 interquartile ranges outside the
    middle half, and for columns without negatives also on a log scale, so ordinary
    long-tailed data (incomes, order amounts) is left alone. Wild values, more
    than 10 ranges out, are a warning. Milder ones are a note, and only when rare.
    """
    values = numeric_values(df, column, kind)
    if values is None or len(values) < 20:
        return []
    values = values.astype(float)
    distance = _spread_distance(values)
    if distance is None:
        return []
    far = distance > 3
    wild = distance > 10
    if far.any() and values.min() >= 0:
        log_distance = _spread_distance(np.log1p(values))
        if log_distance is not None:
            far &= log_distance > 3
            wild &= log_distance > 5
    if already:
        keep = ~values.index.isin(list(already))
        far &= keep
        wild &= keep

    q1, q3 = values.quantile(0.25), values.quantile(0.75)
    usual = f"most rows are between {num(q1)} and {num(q3)}"
    rare_limit = max(5, 0.001 * len(values))
    findings = []

    wild_values = values[wild].sort_values(key=lambda s: -distance[s.index])
    if 0 < len(wild_values) <= rare_limit:
        findings.append(
            Finding(
                WARNING, "extreme", str(column),
                f"{column} has {n(len(wild_values), 'value')} wildly outside the usual range "
                f"({usual}): {show(wild_values.unique())}.",
                count=len(wild_values), examples=list(wild_values.unique()[:5]), rows=wild_values.index,
                why="More than 10 times the middle spread away from it. Often a typing or unit mistake.",
            )
        )
        far &= ~wild

    mild = values[far]
    if 0 < len(mild) <= rare_limit:
        findings.append(
            Finding(
                NOTE, "unusual", str(column),
                f"{column} has {n(len(mild), 'unusually large or small value')} "
                f"({usual}): {show(mild.unique())}.",
                count=len(mild), examples=list(mild.unique()[:5]), rows=mild.index,
                why="More than 3 times the middle spread away from it, and rare. May be correct.",
            )
        )
    return findings


def run_standalone(df: pd.DataFrame, kinds: Dict[str, str], today=None, baselined=()) -> List[Finding]:
    """
    Run every history-free check. Columns named in ``baselined`` skip the checks
    that a comparison with the baseline does better (missing values, extremes).
    """
    findings = check_structure(df, kinds)
    if len(df) == 0:
        return findings
    for column in df.columns:
        kind = kinds[column]
        found = []
        found += check_unique_id(df, column, kind)
        found += check_spelling(df, column, kind)
        found += check_email(df, column, kind)
        found += check_dates(df, column, kind, today=today)
        found += check_number_text(df, column, kind)
        impossible = check_impossible(df, column, kind)
        found += impossible
        if column not in baselined:
            found += check_missing(df, column, kind)
            flagged = set()
            for finding in impossible:
                flagged.update(finding.rows)
            found += check_extremes(df, column, kind, already=flagged)
        findings += found
    return findings
