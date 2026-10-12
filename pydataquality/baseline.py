"""
The baseline: what a "normal" file looks like, learned from one the user
approved, and the comparison of a new file against it.

A baseline is a small YAML file meant to be read and edited by hand. The
``rules`` and ``ignore`` sections belong to the user and survive re-accepting.
"""

import datetime as _dt
import os
import re
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from . import semantic as sem
from .standalone import (
    ALL_COLUMNS,
    NOTE,
    PROBLEM,
    WARNING,
    Finding,
    duplicate_mask,
    n,
    num,
    numeric_values,
    show,
)

BASELINE_DIR = ".pdq"
MAX_CATEGORY_VALUES = 50

_NOISE_WORDS = {
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "sept", "oct",
    "nov", "dec", "january", "february", "march", "april", "june", "july",
    "august", "september", "october", "november", "december", "final", "copy",
    "new", "latest", "updated", "export", "q1", "q2", "q3", "q4",
}


# --------------------------------------------------------------------------
# Naming and storage
# --------------------------------------------------------------------------
def dataset_name(path: str) -> str:
    """
    'Orders_November_2026 (1).csv' -> 'orders'. Lets this month's file find the
    baseline saved from last month's without the user naming anything.
    """
    stem = os.path.splitext(os.path.basename(str(path)))[0].lower()
    words = [w for w in re.split(r"[^a-z0-9]+", stem) if w]
    kept = [
        w for w in words
        if w not in _NOISE_WORDS and not w.isdigit() and not re.fullmatch(r"v\d+|\d+[a-z]{0,2}", w)
    ]
    return "_".join(kept) or "_".join(words) or "data"


def baseline_path(data_path: str, name: Optional[str] = None) -> str:
    folder = os.path.join(os.path.dirname(os.path.abspath(data_path)), BASELINE_DIR)
    return os.path.join(folder, f"{name or dataset_name(data_path)}.yml")


def find_baseline(data_path: str, columns) -> Optional[str]:
    """
    The baseline for a data file: one saved under the same dataset name, or
    failing that, the saved baseline whose columns best match (80% or more).
    """
    exact = baseline_path(data_path)
    if os.path.isfile(exact):
        return exact
    folder = os.path.dirname(exact)
    if not os.path.isdir(folder):
        return None
    columns = {str(c) for c in columns}
    best, best_score = None, 0.8
    for filename in sorted(os.listdir(folder)):
        if not filename.endswith(".yml"):
            continue
        candidate = os.path.join(folder, filename)
        try:
            known = set(load(candidate).get("columns", {}))
        except Exception:
            continue
        if not known:
            continue
        score = len(columns & known) / len(columns | known)
        if score >= best_score:
            best, best_score = candidate, score
    return best


def load(path: str) -> Dict:
    import yaml

    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict) or "columns" not in data:
        raise ValueError(f"{path} is not a PyDataQuality baseline file")
    return data


def save(baseline: Dict, path: str) -> str:
    import yaml

    if os.path.isfile(path):  # keep what the user wrote by hand
        try:
            previous = load(path)
            for section in ("rules", "ignore"):
                if section in previous and section not in baseline:
                    baseline[section] = previous[section]
        except Exception:
            pass
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    header = (
        "# PyDataQuality baseline: what a normal file looks like.\n"
        "# Learned automatically. You can edit it. Add your own checks under 'rules', e.g.\n"
        "#   rules:\n"
        "#     price: [greater than 0]\n"
        "#     order_id: [unique, not empty]\n"
        "#     status: [one of paid, pending, refunded]\n"
    )
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(header)
        yaml.safe_dump(baseline, handle, sort_keys=False, allow_unicode=True, default_flow_style=None, width=100)
    return path


# --------------------------------------------------------------------------
# Learning
# --------------------------------------------------------------------------
def value_type(series: pd.Series, kind: str) -> str:
    """What a reader would call the column's type."""
    if kind == sem.EMPTY:
        return "empty"
    if kind == sem.BOOLEAN:
        return "true/false values"
    if kind == sem.DATE:
        return "dates"
    if pd.api.types.is_numeric_dtype(series):
        return "numbers"
    return "text"


def _plain(value):
    """Convert numpy scalars so the YAML stays readable."""
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return round(float(value), 6)
    return value


def _dates(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series.dropna()
    return sem.parse_dates(sem.as_text(series)).dropna()


def fingerprint(df: pd.DataFrame) -> str:
    try:
        total = int(pd.util.hash_pandas_object(df, index=False).sum())
    except TypeError:
        total = int(pd.util.hash_pandas_object(df.astype(str), index=False).sum())
    return f"{total & 0xFFFFFFFFFFFFFFFF:016x}"


def learn(df: pd.DataFrame, kinds: Dict[str, str], name: str = "data", source: str = "") -> Dict:
    """Describe a file the user has approved."""
    columns = {}
    distinct = df[~duplicate_mask(df)] if len(df) else df
    for column in df.columns:
        series, kind = df[column], kinds[column]
        info = {
            "kind": kind,
            "type": value_type(series, kind),
            "missing_pct": round(float(series.isna().mean() * 100), 2) if len(df) else 0.0,
        }
        present = distinct[column].dropna()
        if len(present) >= 2 and kind != sem.BOOLEAN and present.is_unique:
            info["unique"] = True

        numbers = numeric_values(df, column, kind)
        if numbers is not None and len(numbers):
            info["min"] = _plain(numbers.min())
            info["max"] = _plain(numbers.max())
            info["median"] = _plain(numbers.median())
            if numbers.nunique() > 10:
                edges = np.unique(np.percentile(numbers, np.linspace(0, 100, 11)))
                if len(edges) > 2:
                    shares = _shares(numbers, edges[1:-1])
                    info["bins"] = [_plain(e) for e in edges[1:-1]]
                    info["shares"] = [round(float(s), 4) for s in shares]
        elif kind == sem.CATEGORY:
            values = sem.as_text(series)
            distinct_values = sorted(values.unique().tolist())
            if len(distinct_values) <= MAX_CATEGORY_VALUES:
                info["values"] = distinct_values
        elif kind == sem.DATE:
            dates = _dates(series)
            if len(dates):
                info["earliest"] = str(dates.min().date())
                info["latest"] = str(dates.max().date())
        columns[str(column)] = info

    return {
        "version": 1,
        "name": name,
        "learned_from": os.path.basename(source) if source else "",
        "learned_on": _dt.date.today().isoformat(),
        "rows": int(len(df)),
        "fingerprint": fingerprint(df),
        "columns": columns,
    }


def _shares(values: pd.Series, inner_edges) -> np.ndarray:
    edges = np.concatenate(([-np.inf], np.asarray(inner_edges, dtype=float), [np.inf]))
    counts, _ = np.histogram(values.astype(float), bins=edges)
    return counts / max(len(values), 1)


def psi(expected: np.ndarray, actual: np.ndarray) -> float:
    """Population Stability Index between two sets of bin shares."""
    eps = 1e-4
    expected = np.where(np.asarray(expected, dtype=float) <= 0, eps, expected)
    actual = np.where(np.asarray(actual, dtype=float) <= 0, eps, actual)
    return float(np.sum((actual - expected) * np.log(actual / expected)))


# --------------------------------------------------------------------------
# Comparing a new file with the baseline
# --------------------------------------------------------------------------
def compare(df: pd.DataFrame, kinds: Dict[str, str], baseline: Dict) -> List[Finding]:
    findings: List[Finding] = []
    known: Dict[str, Dict] = baseline.get("columns", {})
    current = {str(c): c for c in df.columns}
    source = baseline.get("learned_from") or "the baseline"

    if len(df) and baseline.get("fingerprint") == fingerprint(df):
        findings.append(
            Finding(
                WARNING, "same_file", ALL_COLUMNS,
                f"This file has exactly the same contents as {source}. You may have been sent the old file again.",
            )
        )

    missing = [c for c in known if c not in current]
    if missing:
        verb = "is" if len(missing) == 1 else "are"
        findings.append(
            Finding(
                PROBLEM, "column_missing", ALL_COLUMNS,
                f"{n(len(missing), 'column')} {verb} missing: {', '.join(missing)}. "
                f"{'It was' if len(missing) == 1 else 'They were'} in {source}.",
                count=len(missing), examples=missing,
            )
        )
    added = [c for c in current if c not in known]
    if added:
        findings.append(
            Finding(
                WARNING, "column_new", ALL_COLUMNS,
                f"{n(len(added), 'new column')} not seen before: {', '.join(added)}.",
                count=len(added), examples=added,
            )
        )

    before_rows = baseline.get("rows") or 0
    if before_rows and len(df) and not 0.5 <= len(df) / before_rows <= 2.0:
        change = len(df) / before_rows - 1
        direction = "more" if change > 0 else "fewer"
        findings.append(
            Finding(
                WARNING, "row_count", ALL_COLUMNS,
                f"The file has {n(len(df), 'row')}. Last time it had {before_rows:,} "
                f"({abs(change):.0%} {direction}).",
                count=len(df),
            )
        )

    distinct = df[~duplicate_mask(df)] if len(df) else df
    for name, info in known.items():
        if name not in current or len(df) == 0:
            continue
        column = current[name]
        series, kind = df[column], kinds[column]
        findings += _compare_column(df, distinct, column, series, kind, info)
    return findings


def _compare_column(df, distinct, column, series, kind, info) -> List[Finding]:
    findings = []
    label = str(column)

    now_type, before_type = value_type(series, kind), info.get("type")
    if before_type and now_type != before_type and "empty" not in (now_type, before_type):
        findings.append(
            Finding(
                PROBLEM, "type_changed", label,
                f"{label} used to hold {before_type}. Now it holds {now_type}.",
                count=int(series.notna().sum()),
            )
        )

    missing = series.isna()
    now_pct, before_pct = float(missing.mean() * 100), float(info.get("missing_pct", 0))
    jump = now_pct - before_pct
    if jump >= 10:
        findings.append(
            Finding(
                PROBLEM if jump >= 40 else WARNING, "missing_jump", label,
                f"{label} is empty in {now_pct:.0f}% of rows. Last time it was {before_pct:.0f}%.",
                count=int(missing.sum()), rows=df.index[missing],
            )
        )

    if info.get("unique"):
        present = distinct[column].dropna()
        repeated = present[present.duplicated(keep=False)]
        if len(repeated):
            findings.append(
                Finding(
                    PROBLEM, "not_unique", label,
                    f"{label} had no repeats last time. Now {n(repeated.nunique(), 'value appears', 'values appear')} "
                    f"more than once, e.g. {show(repeated.unique())}.",
                    count=len(repeated), examples=list(repeated.unique()[:5]), rows=repeated.index,
                    why="Exact duplicate rows are reported separately and not counted here.",
                )
            )

    if "values" in info and kind in (sem.CATEGORY, sem.TEXT, sem.BOOLEAN):
        text = sem.as_text(series)
        unseen = text[~text.isin([str(v) for v in info["values"]])]
        if len(unseen):
            findings.append(
                Finding(
                    WARNING, "new_values", label,
                    f"{label} has {n(unseen.nunique(), 'value')} never seen before: {show(unseen.unique(), 4)} "
                    f"({n(len(unseen), 'row')}).",
                    count=len(unseen), examples=list(unseen.unique()[:5]), rows=unseen.index,
                )
            )

    numbers = numeric_values(df, column, kind)
    if numbers is not None and len(numbers) and "min" in info and "max" in info:
        low, high = float(info["min"]), float(info["max"])
        margin = 0.1 * (high - low)
        outside = numbers[(numbers < low - margin) | (numbers > high + margin)]
        if len(outside):
            findings.append(
                Finding(
                    WARNING, "out_of_range", label,
                    f"{label} has {n(len(outside), 'value')} outside the range seen before "
                    f"({num(low)} to {num(high)}): {show(outside.unique())}.",
                    count=len(outside), examples=list(outside.unique()[:5]), rows=outside.index,
                    why="A 10% margin is allowed beyond the smallest and largest values in the baseline.",
                )
            )
        if "bins" in info and len(numbers) >= 100:
            shift = psi(np.array(info["shares"]), _shares(numbers, info["bins"]))
            if shift >= 0.25:
                findings.append(
                    Finding(
                        WARNING, "shifted", label,
                        f"{label} values have shifted. The typical value was {num(info.get('median', 0))}, "
                        f"now it is {num(numbers.median())}.",
                        count=len(numbers),
                        why=f"Population Stability Index is {shift:.2f}; 0.25 or more counts as a large change.",
                    )
                )

    if kind == sem.DATE and info.get("latest"):
        dates = _dates(series)
        if len(dates) and dates.max() < pd.Timestamp(info["earliest"]):
            findings.append(
                Finding(
                    NOTE, "older_dates", label,
                    f"Every date in {label} is before {info['earliest']}, the earliest date last time.",
                )
            )
    return findings


# --------------------------------------------------------------------------
# The user's own rules
# --------------------------------------------------------------------------
_NUM = r"(-?\d+(?:\.\d+)?)"


def _other_side(df, operand: str):
    """A rule's right-hand side: another column, 'today', a number, or a date."""
    operand = operand.strip()
    if operand in df.columns:
        return df[operand]
    if operand.lower() == "today":
        return pd.Timestamp.now().normalize()
    try:
        return float(operand)
    except ValueError:
        return pd.Timestamp(operand)


def _comparable(series: pd.Series, other):
    """Bring a column and a rule operand to the same type."""
    other_is_date = isinstance(other, pd.Timestamp) or (
        isinstance(other, pd.Series) and not pd.api.types.is_numeric_dtype(other)
    )
    if other_is_date:
        left = _dates_aligned(series)
        right = _dates_aligned(other) if isinstance(other, pd.Series) else other
        return left, right
    left = series if pd.api.types.is_numeric_dtype(series) else sem.to_number(sem.as_text(series))
    return left.reindex(series.index), other


def _dates_aligned(series: pd.Series) -> pd.Series:
    if pd.api.types.is_datetime64_any_dtype(series):
        return series
    return sem.parse_dates(sem.as_text(series)).reindex(series.index)


def rule_mask(df: pd.DataFrame, column, rule: str) -> pd.Series:
    """
    Rows that break one rule. Raises ValueError for a rule that cannot be
    understood, so that a typo is reported instead of silently passing.
    """
    series = df[column]
    present = series.notna()
    text = " ".join(str(rule).strip().split())
    lowered = text.lower()

    if lowered == "unique":
        return present & series.duplicated(keep=False)
    if lowered in ("not empty", "required", "not missing"):
        return ~present | (series.astype(str).str.strip() == "")
    if lowered == "is email":
        return present & ~series.astype(str).str.strip().map(lambda v: bool(sem.EMAIL_RE.match(v)))
    if lowered == "is date":
        return present & sem.date_shapes(series.astype(str).str.strip()).isna()
    if lowered == "not in the future":
        return present & (_dates_aligned(series) > pd.Timestamp.now())

    match = re.fullmatch(rf"between {_NUM} and {_NUM}", lowered)
    if match:
        low, high = float(match.group(1)), float(match.group(2))
        left, _ = _comparable(series, 0.0)
        return present & ~((left >= low) & (left <= high))

    if lowered.startswith("one of "):
        allowed = {v.strip().casefold() for v in text[len("one of "):].split(",") if v.strip()}
        return present & ~series.astype(str).str.strip().str.casefold().isin(allowed)

    if lowered.startswith("matches "):
        pattern = re.compile(text[len("matches "):].strip())
        return present & ~series.astype(str).map(lambda v: bool(pattern.fullmatch(v)))

    comparisons = [
        ("greater than ", lambda a, b: a > b), ("more than ", lambda a, b: a > b),
        ("at least ", lambda a, b: a >= b), ("less than ", lambda a, b: a < b),
        ("at most ", lambda a, b: a <= b), ("on or after ", lambda a, b: a >= b),
        ("on or before ", lambda a, b: a <= b), ("after ", lambda a, b: a > b),
        ("before ", lambda a, b: a < b),
    ]
    for prefix, passes in comparisons:
        if lowered.startswith(prefix):
            try:
                other = _other_side(df, text[len(prefix):])
            except (ValueError, TypeError):
                break
            left, right = _comparable(series, other)
            comparable = left.notna() & (right.notna() if isinstance(right, pd.Series) else True)
            return present & ~(comparable & passes(left, right))

    raise ValueError(f"rule not understood: '{rule}'")


def check_rules(df: pd.DataFrame, rules: Dict) -> List[Finding]:
    findings = []
    for column, column_rules in (rules or {}).items():
        if isinstance(column_rules, str):
            column_rules = [column_rules]
        if column not in df.columns:
            findings.append(
                Finding(PROBLEM, "rule", str(column), f"There are rules for {column}, but the file has no such column.")
            )
            continue
        for rule in column_rules or []:
            try:
                broken = rule_mask(df, column, rule)
            except (ValueError, re.error) as error:
                findings.append(
                    Finding(
                        PROBLEM, "rule", str(column),
                        f"The rule \"{rule}\" for {column} could not be understood. "
                        "See the README for the rules you can write.",
                        why=str(error),
                    )
                )
                continue
            count = int(broken.sum())
            if count:
                examples = df.loc[broken, column].dropna().unique()[:5]
                suffix = f", e.g. {show(examples)}" if len(examples) else ""
                findings.append(
                    Finding(
                        PROBLEM, "rule", str(column),
                        f"{n(count, 'row breaks', 'rows break')} your rule \"{column}: {rule}\"{suffix}.",
                        count=count, examples=list(examples), rows=df.index[broken],
                    )
                )
    return findings
