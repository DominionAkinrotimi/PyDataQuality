"""
``check``: is this file safe to use, and what changed since the last one?

The result leads with a verdict, lists findings in plain language with the
worst first, and can hand back the affected rows with the reason for each.
"""

import csv
import os
from typing import Dict, Iterable, List, Optional, Union

import pandas as pd

from . import baseline as base
from . import semantic as sem
from .standalone import ALL_COLUMNS, LEVEL_ORDER, NOTE, PROBLEM, WARNING, Finding, n, run_standalone

REASON_COLUMN = "_pdq_reason"

OK, WARNINGS, PROBLEMS = "ok", "warnings", "problems"
EXIT_CODES = {OK: 0, WARNINGS: 1, PROBLEMS: 2}

HEADLINES = {
    # (verdict, has_baseline)
    (PROBLEMS, True): "NOT SAFE TO USE",
    (WARNINGS, True): "CHECK BEFORE USE",
    (OK, True): "LOOKS LIKE LAST TIME",
    (PROBLEMS, False): "PROBLEMS FOUND",
    (WARNINGS, False): "THINGS TO CHECK",
    (OK, False): "NOTHING OBVIOUSLY WRONG",
}


class DataFileError(Exception):
    """The file could not be read. The message is written for the person at the keyboard."""


def load_file(path: str) -> pd.DataFrame:
    """Read CSV, TSV, Excel, JSON or Parquet into a DataFrame."""
    if not os.path.isfile(path):
        raise DataFileError(f"There is no file at {path}")
    extension = os.path.splitext(path)[1].lower()
    try:
        if extension in (".xlsx", ".xlsm", ".xls"):
            try:
                return pd.read_excel(path)
            except ImportError:
                raise DataFileError("Reading Excel files needs one more package. Run: pip install openpyxl")
        if extension == ".parquet":
            try:
                return pd.read_parquet(path)
            except ImportError:
                raise DataFileError("Reading Parquet files needs one more package. Run: pip install pyarrow")
        if extension == ".json":
            return pd.read_json(path)
        return _read_delimited(path)
    except DataFileError:
        raise
    except Exception as error:
        raise DataFileError(f"Could not read {os.path.basename(path)}: {error}")


def _read_delimited(path: str) -> pd.DataFrame:
    last_error = None
    for encoding in ("utf-8-sig", "cp1252", "latin-1"):
        try:
            with open(path, "r", encoding=encoding, newline="") as handle:
                head = handle.read(64 * 1024)
            try:
                separator = csv.Sniffer().sniff(head, delimiters=",;\t|").delimiter
            except csv.Error:
                separator = "\t" if path.lower().endswith(".tsv") else ","
            return pd.read_csv(path, sep=separator, encoding=encoding)
        except UnicodeDecodeError as error:
            last_error = error
    raise last_error


class CheckResult:
    """Outcome of :func:`check`."""

    def __init__(self, df, findings, name, baseline=None, baseline_source=None, kinds=None, hidden=0):
        self.df = df
        self.findings: List[Finding] = sorted(findings, key=lambda f: (LEVEL_ORDER[f.level], -f.count))
        self.name = name
        self.baseline = baseline
        self.baseline_source = baseline_source
        self.kinds = kinds or {}
        self.hidden = hidden  # findings silenced by the baseline's ignore list

    # -- summary ----------------------------------------------------------
    @property
    def has_baseline(self) -> bool:
        return self.baseline is not None

    @property
    def problems(self) -> List[Finding]:
        return [f for f in self.findings if f.level == PROBLEM]

    @property
    def warnings(self) -> List[Finding]:
        return [f for f in self.findings if f.level == WARNING]

    @property
    def notes(self) -> List[Finding]:
        return [f for f in self.findings if f.level == NOTE]

    @property
    def verdict(self) -> str:
        if self.problems:
            return PROBLEMS
        return WARNINGS if self.warnings else OK

    @property
    def headline(self) -> str:
        return HEADLINES[(self.verdict, self.has_baseline)]

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.verdict]

    @property
    def ok(self) -> bool:
        return self.verdict == OK

    def __bool__(self) -> bool:
        return self.ok

    def clean_columns(self) -> List[str]:
        flagged = {f.column for f in self.findings}
        for finding in self.findings:
            if finding.code == "column_new":
                flagged.update(finding.examples)
        return [str(c) for c in self.df.columns if str(c) not in flagged]

    # -- rows -------------------------------------------------------------
    def bad_rows(self, include_notes: bool = False) -> pd.DataFrame:
        """The affected rows, with a ``_pdq_reason`` column saying why each is listed."""
        reasons: Dict = {}
        for finding in self.findings:
            if finding.rows is None or (finding.level == NOTE and not include_notes):
                continue
            label = finding.code.replace("_", " ")
            if finding.column != ALL_COLUMNS:
                label = f"{finding.column}: {label}"
            for index in finding.rows:
                reasons.setdefault(index, []).append(label)
        rows = self.df.loc[[i for i in self.df.index if i in reasons]].copy()
        rows[REASON_COLUMN] = ["; ".join(reasons[i]) for i in rows.index]
        return rows

    # -- output -----------------------------------------------------------
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "verdict": self.verdict,
            "headline": self.headline,
            "rows": int(len(self.df)),
            "columns": int(len(self.df.columns)),
            "compared_with": (self.baseline or {}).get("learned_from") or None,
            "has_baseline": self.has_baseline,
            "problems": len(self.problems),
            "warnings": len(self.warnings),
            "notes": len(self.notes),
            "affected_rows": int(len(self.bad_rows())),
            "clean_columns": self.clean_columns(),
            "findings": [f.to_dict() for f in self.findings],
        }

    def to_text(self, color: bool = False, why: bool = False, unicode: bool = True) -> str:
        paint = _painter(color)
        mark = {PROBLEMS: "✖", WARNINGS: "!", OK: "✓"} if unicode else {PROBLEMS: "X", WARNINGS: "!", OK: "OK"}
        tone = {PROBLEMS: "red", WARNINGS: "yellow", OK: "green"}[self.verdict]

        counts = []
        if self.problems:
            counts.append(n(len(self.problems), "problem"))
        if self.warnings:
            counts.append(n(len(self.warnings), "warning"))
        lines = [
            paint(f"{mark[self.verdict]} {self.headline}", tone, bold=True)
            + (f"   {', '.join(counts)}" if counts else "")
        ]
        size = f"{n(len(self.df), 'row')}, {n(len(self.df.columns), 'column')}"
        if self.has_baseline:
            source = self.baseline.get("learned_from") or self.baseline.get("name") or "the baseline"
            lines.append(paint(f"  {self.name}: {size}. Compared with {source}.", "dim"))
        else:
            lines.append(paint(f"  {self.name}: {size}. No earlier file to compare with.", "dim"))

        number = 0
        for title, tone, group in (
            ("PROBLEMS", "red", self.problems),
            ("WARNINGS", "yellow", self.warnings),
            ("ALSO NOTED", "dim", self.notes),
        ):
            if not group:
                continue
            lines += ["", paint(title, tone, bold=True)]
            for finding in group:
                number += 1
                lines.append(f" {number:>2}  {finding.message}")
                if why:
                    detail = f"{finding.why} " if finding.why else ""
                    lines.append(paint(f"       {detail}[{finding.key}]", "dim"))

        clean = self.clean_columns()
        if clean and self.findings:
            label = "UNCHANGED" if self.has_baseline else "NO ISSUES IN"
            shown = ", ".join(clean[:6]) + (f" and {len(clean) - 6} more" if len(clean) > 6 else "")
            lines += ["", paint(label, "green", bold=True) + f"  {shown}"]
        if self.hidden:
            lines.append(paint(f"  {n(self.hidden, 'finding')} hidden by the ignore list in the baseline.", "dim"))
        return "\n".join(lines)

    def __repr__(self) -> str:
        return self.to_text()

    def __str__(self) -> str:
        return self.to_text()


def _painter(enabled: bool):
    codes = {"red": "31", "yellow": "33", "green": "32", "dim": "2", "blue": "34"}

    def paint(text, tone, bold=False):
        if not enabled:
            return text
        prefix = f"\033[{'1;' if bold else ''}{codes[tone]}m"
        return f"{prefix}{text}\033[0m"

    return paint


def _resolve_baseline(baseline, path, columns):
    """Returns (baseline dict or None, where it came from or None)."""
    if isinstance(baseline, dict):
        return baseline, None
    if isinstance(baseline, str):
        if os.path.isfile(baseline):
            return base.load(baseline), baseline
        if path:  # a dataset name rather than a file path
            named = base.baseline_path(path, baseline)
            if os.path.isfile(named):
                return base.load(named), named
        raise DataFileError(f"There is no baseline at {baseline}")
    if baseline is None and path:
        found = base.find_baseline(path, columns)
        if found:
            return base.load(found), found
    return None, None


def check(
    data: Union[str, pd.DataFrame],
    baseline: Union[None, bool, str, Dict] = None,
    rules: Optional[Dict] = None,
    columns: Optional[Iterable[str]] = None,
    only: Optional[Iterable[str]] = None,
    name: Optional[str] = None,
    today=None,
) -> CheckResult:
    """
    Check a data file or DataFrame.

    Parameters
    ----------
    data : str or pandas.DataFrame
        A file path (CSV, TSV, Excel, JSON, Parquet) or a DataFrame.
    baseline : None, False, str or dict
        ``None`` looks for a saved baseline next to the file. ``False`` never
        compares. A path, a dataset name or a baseline dict uses that one.
    rules : dict, optional
        Your own checks, ``{column: [rule, ...]}``, e.g. ``{"price": ["greater than 0"]}``.
        Added to any rules stored in the baseline.
    columns : list of str, optional
        Only report findings about these columns.
    only : list of str, optional
        Only report these kinds of finding, by code (e.g. ``["duplicates", "spelling"]``).
    name : str, optional
        Label for the output. Defaults to the file name.

    Returns
    -------
    CheckResult
    """
    path = data if isinstance(data, str) else None
    df = load_file(path) if path else data
    if not isinstance(df, pd.DataFrame):
        raise TypeError("check() needs a file path or a pandas DataFrame")
    label = name or (os.path.basename(path) if path else "DataFrame")

    kinds = sem.infer_kinds(df)
    known, source = (None, None) if baseline is False else _resolve_baseline(baseline, path, df.columns)

    baselined = set()
    if known:
        baselined = {c for c in df.columns if str(c) in known.get("columns", {})}
    findings = run_standalone(df, kinds, today=today, baselined=baselined)
    if known:
        findings += base.compare(df, kinds, known)
        # The comparison says the same thing with more context
        compared = {f.column for f in findings if f.code == "not_unique"}
        findings = [f for f in findings if not (f.code == "id_repeats" and f.column in compared)]

    all_rules = dict((known or {}).get("rules") or {})
    for column, extra in (rules or {}).items():
        extra = [extra] if isinstance(extra, str) else list(extra)
        existing = all_rules.get(column) or []
        existing = [existing] if isinstance(existing, str) else list(existing)
        all_rules[column] = existing + extra
    findings += base.check_rules(df, all_rules)

    ignored = {str(item).strip() for item in ((known or {}).get("ignore") or [])}
    kept = [f for f in findings if f.key not in ignored]
    hidden = len(findings) - len(kept)
    if columns:
        wanted = {str(c) for c in columns}
        kept = [f for f in kept if f.column in wanted]
    if only:
        wanted_codes = {str(c).strip().lower().replace(" ", "_") for c in only}
        kept = [f for f in kept if f.code in wanted_codes]

    return CheckResult(df, kept, label, baseline=known, baseline_source=source, kinds=kinds, hidden=hidden)


def accept(data: Union[str, pd.DataFrame], path: Optional[str] = None, name: Optional[str] = None) -> str:
    """
    Remember a file as normal. Later files of the same kind are compared with it.

    Returns the path of the baseline file. For a DataFrame, ``path`` is required.
    """
    source = data if isinstance(data, str) else ""
    df = load_file(source) if source else data
    if path is None:
        if not source:
            raise ValueError("accept() needs a path for the baseline when given a DataFrame")
        path = base.baseline_path(source, name)
    dataset = name or (base.dataset_name(source) if source else os.path.splitext(os.path.basename(path))[0])
    learned = base.learn(df, sem.infer_kinds(df), name=dataset, source=source)
    return base.save(learned, path)
