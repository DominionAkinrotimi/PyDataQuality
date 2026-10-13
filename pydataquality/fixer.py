"""
Fix what a check found, and save a corrected copy.

Three promises:

1. The original file is never changed. Fixes are applied to a copy.
2. Nothing is fixed without being offered first. ``propose`` lists what can be
   done about each finding. Only the fixes that are safe for any file (removing
   exact copies of a row, using one spelling for a value) are recommended. The
   rest need a decision, because only the person who knows the data can make
   it: an impossible age can be emptied or its row removed, but the tool cannot
   know what the age should have been.
3. Every change is written down: which row, which column, what it was and what
   it became.

Some findings cannot be fixed at all from inside the file: a missing column, far
fewer rows than last time, an email address that is simply wrong. Those are left
for whoever produced the data.
"""

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pandas as pd

from . import semantic as sem
from .standalone import ALL_COLUMNS, Finding, n, show, spelling_map

REMOVE = "remove_rows"
REPLACE = "replace"
BLANK = "blank"
REFORMAT = "reformat"

# Findings about a single cell being wrong, where the choice is to empty the cell or drop the row
CELL_CODES = {
    "impossible", "negative", "future_date", "bad_date", "bad_email", "not_a_number",
    "extreme", "out_of_range", "rule",
}
REPEAT_CODES = {"id_repeats", "not_unique"}

DATE_FORMATS = {
    "2024-01-31": "%Y-%m-%d",
    "2024/01/31": "%Y/%m/%d",
    "31/01/2024": "%d/%m/%Y",
    "31-01-2024": "%d-%m-%Y",
    "31.01.2024": "%d.%m.%Y",
    "31 Jan 2024": "%d %b %Y",
    "Jan 31, 2024": "%b %d, %Y",
}
_HAS_TIME = re.compile(r"\d:\d\d")


@dataclass
class Option:
    """One thing that can be done about a finding."""

    action: str
    label: str
    detail: str
    recommended: bool = False
    rows: int = 0  # rows that would be removed
    cells: int = 0  # cells that would be changed
    examples: List[List[str]] = field(default_factory=list)  # [before, after]

    def to_dict(self) -> Dict:
        return {
            "action": self.action, "label": self.label, "detail": self.detail,
            "recommended": self.recommended, "rows": int(self.rows), "cells": int(self.cells),
            "examples": self.examples,
        }


@dataclass
class Proposal:
    """A finding and what can be done about it. No options means it cannot be fixed here."""

    key: str
    level: str
    column: str
    message: str
    options: List[Option] = field(default_factory=list)
    reason: str = ""  # why there is nothing to offer

    def to_dict(self) -> Dict:
        return {
            "key": self.key, "level": self.level, "column": self.column, "message": self.message,
            "options": [o.to_dict() for o in self.options], "reason": self.reason,
        }


@dataclass
class Change:
    row: object  # the row number as the file shows it
    column: str
    before: str
    after: str
    reason: str


@dataclass
class FixOutcome:
    df: pd.DataFrame  # the corrected copy
    changes: List[Change]
    removed_rows: int
    changed_cells: int
    applied: List[str]  # keys of the findings that were acted on
    result: object  # the corrected copy, checked again

    def changes_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            [[c.row, c.column, c.before, c.after, c.reason] for c in self.changes],
            columns=["row", "column", "before", "after", "reason"],
        )


def _file_row(index):
    """Row number as a spreadsheet shows it: headings on row 1, first row of data on row 2."""
    try:
        return int(index) + 2
    except (TypeError, ValueError):
        return index


def _text(value) -> str:
    return "" if value is None or (isinstance(value, float) and value != value) else str(value)


def _date_plan(series: pd.Series, rows) -> Dict:
    """For a column that mixes date layouts: {index label: the date rewritten in the main layout}."""
    text = sem.as_text(series)
    text = text[text != ""]
    shapes = sem.date_shapes(text)
    counts = shapes.dropna().value_counts()
    if len(counts) < 2 or counts.index[0] not in DATE_FORMATS:
        return {}
    layout = DATE_FORMATS[counts.index[0]]
    wanted = text[text.index.isin(rows)]
    wanted = wanted[~wanted.str.contains(_HAS_TIME)]  # a time of day is left exactly as written
    parsed = sem.parse_dates(wanted).dropna()
    return {index: stamp.strftime(layout) for index, stamp in parsed.items()}


def _later_repeats(df: pd.DataFrame, column, rows) -> pd.Index:
    """Of the rows sharing an identifier, every one after the first."""
    values = df.loc[df.index.isin(rows), column]
    return values.index[values.duplicated(keep="first")]


def propose(result) -> List[Proposal]:
    """What can be done about each finding in a check result."""
    df = result.original
    proposals = []
    for finding in result.findings:
        proposal = Proposal(finding.key, finding.level, finding.column, finding.message)
        rows = finding.rows if finding.rows is not None else []
        column = _column(df, finding.column)
        count = len(rows)

        if finding.code == "duplicates" and count:
            proposal.options.append(Option(
                REMOVE, f"Remove the {n(count, 'repeated row')}",
                "The first copy of each row is kept.", recommended=True, rows=count,
            ))
        elif finding.code == "spelling" and column is not None:
            mapping = spelling_map(df[column].dropna().astype(str))
            cells = int(df[column].astype(str).isin(mapping).sum()) if mapping else 0
            if cells:
                pairs = [[before, after] for before, after in list(mapping.items())[:4]]
                proposal.options.append(Option(
                    REPLACE, "Use the most common spelling",
                    f"{show(list(mapping)[:3])} {'becomes' if len(mapping) == 1 else 'become'} the spelling used most often.",
                    recommended=True, cells=cells, examples=pairs,
                ))
        elif finding.code == "mixed_dates" and column is not None:
            plan = _date_plan(df[column], rows)
            if plan:
                pairs = [[_text(df.at[index, column]), after] for index, after in list(plan.items())[:4]]
                proposal.options.append(Option(
                    REFORMAT, "Write them like the rest of the column",
                    "A date such as 03/04/2025 is read with the day first, as 3 April. Check the examples before choosing this.",
                    cells=len(plan), examples=pairs,
                ))
        elif finding.code in REPEAT_CODES and column is not None and count:
            later = _later_repeats(df, column, rows)
            if len(later):
                proposal.options.append(Option(
                    REMOVE, f"Keep the first of each and remove the other {n(len(later), 'row')}",
                    "Only choose this if the later rows really are repeats. They may be different records that were given the same number by mistake.",
                    rows=len(later),
                ))
        elif finding.code in CELL_CODES and column is not None and count:
            pairs = [[_text(value), ""] for value in df.loc[df.index.isin(rows), column].head(4)]
            proposal.options.append(Option(
                BLANK, f"Make {'this cell' if count == 1 else f'these {count:,} cells'} empty",
                "The rows stay. Only the wrong value is taken out.", cells=count, examples=pairs,
            ))
            proposal.options.append(Option(
                REMOVE, f"Remove {'this row' if count == 1 else f'these {count:,} rows'}",
                "The whole row is left out of the corrected copy.", rows=count,
            ))

        if not proposal.options:
            proposal.reason = _why_not(finding)
        proposals.append(proposal)
    return proposals


def _column(df: pd.DataFrame, name: str):
    """The real column label for a finding's column name, or None for whole-file findings."""
    if name == ALL_COLUMNS:
        return None
    for column in df.columns:
        if str(column) == name:
            return column
    return None


def _why_not(finding: Finding) -> str:
    if finding.code in ("column_missing", "column_new", "type_changed", "row_count", "same_file", "no_header", "no_rows"):
        return "This is about the file as a whole. Ask whoever produced it for a corrected one."
    if finding.code in ("missing", "missing_jump", "empty_column"):
        return "The values are not in the file, so there is nothing to correct them with."
    if finding.code == "table_start":
        return "Nothing to fix. The corrected copy starts at the table."
    return "This needs someone who knows the data to decide."


def recommended(proposals: List[Proposal]) -> Dict[str, str]:
    """The choices that are safe for any file: {finding key: action}."""
    return {p.key: o.action for p in proposals for o in p.options if o.recommended}


def apply(result, choices: Optional[Dict[str, str]] = None) -> FixOutcome:
    """
    Apply the chosen fixes to a copy of the data and check the copy again.

    ``choices`` maps a finding's key to an action, e.g.
    ``{"spelling:country": "replace", "impossible:age": "blank"}``. Leave it out
    to apply only the recommended fixes.
    """
    from .checker import check

    proposals = {p.key: p for p in propose(result)}
    if choices is None:
        choices = recommended(list(proposals.values()))

    source = result.original
    fixed = source.copy()
    changes: List[Change] = []
    drop = {}  # index label -> reason
    applied = []
    findings = {f.key: f for f in result.findings}

    for key, action in choices.items():
        proposal, finding = proposals.get(key), findings.get(key)
        if proposal is None or finding is None:
            raise ValueError(f"There is no finding called {key!r} in this result.")
        if action not in {o.action for o in proposal.options}:
            raise ValueError(f"{action!r} is not something that can be done about {key!r}.")
        rows = finding.rows if finding.rows is not None else []
        column = _column(source, finding.column)
        label = finding.code.replace("_", " ")

        if action == REMOVE:
            targets = _later_repeats(source, column, rows) if finding.code in REPEAT_CODES else rows
            for index in targets:
                drop.setdefault(index, label)
        elif action == REPLACE:
            mapping = spelling_map(source[column].dropna().astype(str))
            fixed[column] = fixed[column].astype("object")
            for index, value in source[column].items():
                if _text(value) in mapping and index not in drop:
                    fixed.at[index, column] = mapping[_text(value)]
                    changes.append(Change(_file_row(index), str(column), _text(value), mapping[_text(value)], label))
        elif action == REFORMAT:
            fixed[column] = fixed[column].astype("object")
            for index, after in _date_plan(source[column], rows).items():
                changes.append(Change(_file_row(index), str(column), _text(source.at[index, column]), after, label))
                fixed.at[index, column] = after
        elif action == BLANK:
            if not pd.api.types.is_float_dtype(fixed[column]):
                fixed[column] = fixed[column].astype("object")
            for index in rows:
                changes.append(Change(_file_row(index), str(column), _text(source.at[index, column]), "", label))
                fixed.at[index, column] = None
        applied.append(key)

    # Rows that are being removed do not also need their cells listed
    changes = [c for c in changes if (c.row - 2 if isinstance(c.row, int) else c.row) not in drop]
    cell_changes = len(changes)
    for index, reason in drop.items():
        changes.append(Change(_file_row(index), "(whole row)", "", "removed", reason))
    fixed = fixed.drop(index=list(drop))
    fixed.attrs = dict(source.attrs)
    changes.sort(key=lambda c: (str(type(c.row)), c.row))

    again = check(fixed, baseline=result.baseline if result.baseline is not None else False, name=result.name)
    return FixOutcome(fixed, changes, len(drop), cell_changes, applied, again)


def fixed_name(name: str) -> str:
    """orders.csv -> orders_fixed.csv. Excel stays Excel; everything else is saved as CSV."""
    stem, _, extension = name.rpartition(".")
    if not stem:
        stem, extension = name, ""
    extension = "xlsx" if extension.lower() in ("xlsx", "xlsm", "xls") else "csv"
    return f"{stem}_fixed.{extension}"


def write(df: pd.DataFrame, path: str) -> str:
    """Save a corrected copy. The format follows the file name."""
    if path.lower().endswith(".xlsx"):
        df.to_excel(path, index=False)
    else:
        df.to_csv(path, index=False)
    return path
