"""
A report someone can choose to send when a finding was wrong.

PyDataQuality sends nothing anywhere, so the only way its makers learn that a
finding was a false alarm is if the person tells them. This module writes the
text they can copy and send themselves.

The files people check hold salaries, bank transactions, patient records. So
the report is built from a short list of things that are safe by construction,
and nothing else:

- the kind of finding and its level
- what kind of column it was about (a date, a category), never its name
- counts: rows affected, rows and columns in the file
- how many columns of each kind the file has
- the file's type (".csv"), never its name
- the version of PyDataQuality

It never includes a value from the file, an example, a column name, a file
name, a dataset name, or the sentence shown on screen (which quotes values).
``tests/test_feedback.py`` checks that with a file full of recognisable values.
"""

import os
from collections import Counter

from .standalone import ALL_COLUMNS

EMAIL = "contact.dominionakinrotimi@gmail.com"
ISSUES = "https://github.com/DominionAkinrotimi/PyDataQuality/issues/new"

KIND_WORDS = {
    "id": "identifier", "email": "email address", "date": "date", "number": "number",
    "number_as_text": "number stored as text", "boolean": "yes/no", "category": "category",
    "text": "free text", "empty": "empty",
}


def _kind(result, column: str) -> str:
    if column == ALL_COLUMNS:
        return "the whole file"
    for name, kind in result.kinds.items():
        if str(name) == column:
            return KIND_WORDS.get(kind, "unknown")
    return "a column that is not in this file"


def _file_type(name: str) -> str:
    extension = os.path.splitext(str(name))[1].lower()
    return extension if extension in (".csv", ".tsv", ".txt", ".xlsx", ".xlsm", ".xls", ".json", ".parquet") else "not recorded"


def false_alarm_report(result, finding, category: str = "") -> str:
    """The text of a false-alarm report for one finding. Holds nothing from inside the file."""
    from . import __version__

    kinds = Counter(KIND_WORDS.get(kind, "unknown") for kind in result.kinds.values())
    columns = ", ".join(f"{count} {word}" for word, count in sorted(kinds.items()))
    affected = len(finding.rows) if finding.rows is not None else 0
    lines = [
        "PyDataQuality: report of a finding that was wrong",
        "",
        f"Version: {__version__}",
        f"Finding: {finding.code}" + (f" ({category})" if category else ""),
        f"Shown as: {finding.level}",
        f"About: {_kind(result, finding.column)}",
        f"Rows affected: {affected:,} of {len(result.df):,}",
        f"File: {len(result.df):,} rows, {len(result.df.columns):,} columns, type {_file_type(result.name)}",
        f"Columns by kind: {columns or 'none'}",
        f"Compared with an earlier file: {'yes' if result.has_baseline else 'no'}",
        f"Table started on row: {int(result.original.attrs.get('header_row', 1))}",
        "",
        "What was wrong with this finding:",
        "(write a sentence here, in your own words, without pasting values from your file)",
    ]
    return "\n".join(lines)
