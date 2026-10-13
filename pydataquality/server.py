"""
The local app behind ``pdq ui``.

A small JSON API plus the compiled front end in ``static/app``. It serves one
person on their own computer: it listens on 127.0.0.1 only, refuses requests
addressed to any other host name, and requires a per-session token on every
request that reads or changes anything.
"""

import datetime as _dt
import io
import json
import mimetypes
import os
import re
import secrets
import tempfile
import threading
import time
import webbrowser
from collections import OrderedDict
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, List, Optional
from urllib.parse import parse_qs, unquote, urlparse

import numpy as np
import pandas as pd

from . import baseline as base
from . import fixer
from .feedback import false_alarm_report
from . import semantic as sem
from .checker import CheckResult, DataFileError, check, excel_sheets, load_file
from .standalone import ALL_COLUMNS, NOTE
from .webui import report_html

MAX_UPLOAD_BYTES = 300 * 1024 * 1024
MAX_JSON_BYTES = 64 * 1024
ROWS_SHOWN = 200
RESULTS_KEPT = 5
HISTORY_KEPT = 200

HOME = os.path.join(os.path.expanduser("~"), ".pydataquality")
STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "app")
TOKEN_PLACEHOLDER = "__PDQ_TOKEN__"

# Short label shown beside each finding
CATEGORIES = {
    "no_rows": "Structure", "no_header": "Structure", "table_start": "Structure", "empty_column": "Structure",
    "column_missing": "Structure", "column_new": "Structure", "type_changed": "Structure",
    "row_count": "Volume", "same_file": "Volume",
    "duplicates": "Duplicates", "id_repeats": "Identifiers", "not_unique": "Identifiers",
    "missing": "Empty values", "missing_jump": "Empty values",
    "spelling": "Spelling", "new_values": "New values",
    "bad_email": "Format", "bad_date": "Format", "mixed_dates": "Format", "not_a_number": "Format",
    "future_date": "Dates", "older_dates": "Dates",
    "impossible": "Impossible values", "negative": "Impossible values",
    "extreme": "Out of range", "unusual": "Out of range", "out_of_range": "Out of range",
    "shifted": "Shifted values", "rule": "Your rule",
}


class NotFound(Exception):
    pass


class BadRequest(Exception):
    pass


def safe_filename(name: str) -> str:
    name = os.path.basename(str(name).replace("\\", "/")) or "data.csv"
    return re.sub(r"[^A-Za-z0-9._ ()-]", "_", name)[:120]


def safe_dataset_name(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9_-]+", "_", str(name).strip().lower()).strip("_")
    return cleaned[:60] or "data"


def _cell(value) -> str:
    """A table cell as text, the way a spreadsheet would show it."""
    if value is None or (isinstance(value, float) and np.isnan(value)) or value is pd.NaT:
        return ""
    if isinstance(value, float) and value.is_integer() and abs(value) < 1e15:
        return str(int(value))
    return str(value)


def describe_baseline(known: Dict) -> List[Dict]:
    """What was learned about each column, in words, for the review screen."""
    described = []
    skipped = set(known.get("skip") or [])
    for name, info in (known.get("columns") or {}).items():
        holds = [info.get("type", "values")]
        checks = []
        if info.get("unique"):
            holds.append("no repeats")
            checks.append("must stay unique")
        if "values" in info:
            values = [str(v) for v in info["values"]]
            shown = ", ".join(values[:4]) + (f" and {len(values) - 4} more" if len(values) > 4 else "")
            holds.append(f"{len(values)} value{'s' if len(values) != 1 else ''}: {shown}")
            checks.append("new values are flagged")
        if "min" in info and "max" in info and info.get("kind") != sem.ID:
            holds.append(f"{base.num(info['min'])} to {base.num(info['max'])}")
            checks.append("values far outside this range are flagged")
        if info.get("earliest"):
            holds.append(f"{info['earliest']} to {info['latest']}")
        empty = float(info.get("missing_pct") or 0)
        if empty >= 1:
            holds.append(f"{empty:.0f}% empty")
        checks.append("flagged if it disappears, changes type or becomes much emptier")
        described.append(
            {"name": name, "holds": ", ".join(holds), "checks": checks, "checked": name not in skipped}
        )
    return described


def sample_frame() -> pd.DataFrame:
    """A small, deliberately messy customer file for first-time users."""
    rng = np.random.default_rng(11)
    n = 480
    frame = pd.DataFrame(
        {
            "customer_id": np.arange(1001, 1001 + n),
            "full_name": [f"Customer {i}" for i in range(n)],
            "age": rng.integers(19, 68, n),
            "email": [f"customer{i}@example.com" for i in range(n)],
            "country": rng.choice(["Nigeria", "Ghana", "Kenya", "South Africa"], n, p=[0.5, 0.2, 0.2, 0.1]),
            "signup_date": pd.date_range("2025-01-06", periods=n, freq="D").strftime("%Y-%m-%d"),
            "monthly_spend": rng.lognormal(4.2, 0.45, n).round(2),
        }
    )
    frame.loc[[14, 207], "age"] = [999, -4]
    frame.loc[[33, 34, 35, 290], "email"] = ["none", "n/a", "ada.at.example.com", "unknown"]
    frame.loc[frame.index[60:84], "country"] = "nigeria "
    frame.loc[frame.index[120:126], "country"] = "NIGERIA"
    frame.loc[[402, 403, 404], "signup_date"] = ["2031-02-11", "2031-02-12", "2030-12-01"]
    frame.loc[[150, 151], "signup_date"] = ["03/04/2025", "17/05/2025"]
    frame.loc[77, "monthly_spend"] = 480000.0
    frame = pd.concat([frame, frame.iloc[200:206]], ignore_index=True)
    return frame


class App:
    """State for one running app."""

    def __init__(self, home: str = HOME):
        self.token = secrets.token_urlsafe(24)
        self.home = home
        self.store = os.path.join(home, "baselines")
        self.history_path = os.path.join(home, "history.jsonl")
        self.workdir = tempfile.TemporaryDirectory(prefix="pdq_")
        self.results: "OrderedDict[str, Dict]" = OrderedDict()
        self.pending: Dict[str, Dict] = {}  # uploads waiting for a sheet to be chosen
        self.lock = threading.Lock()

    def close(self) -> None:
        self.workdir.cleanup()

    # -- history ----------------------------------------------------------
    def history(self) -> List[Dict]:
        if not os.path.isfile(self.history_path):
            return []
        entries = []
        with open(self.history_path, "r", encoding="utf-8") as handle:
            for line in handle:
                try:
                    entry = json.loads(line)
                    if isinstance(entry, dict):
                        entries.append(entry)
                except ValueError:
                    continue  # a damaged line never blocks the app
        return entries[-HISTORY_KEPT:]

    def _write_history(self, entries: List[Dict]) -> None:
        os.makedirs(self.home, exist_ok=True)
        with open(self.history_path, "w", encoding="utf-8") as handle:
            for entry in entries[-HISTORY_KEPT:]:
                handle.write(json.dumps(entry) + "\n")

    def _remember(self, result: CheckResult, dataset: str, result_id: str) -> None:
        entry = {
            "id": result_id,
            "when": _dt.datetime.now().isoformat(timespec="seconds"),
            "dataset": dataset,
            "file": result.name,
            "verdict": result.verdict,
            "headline": result.headline,
            "problems": len(result.problems),
            "warnings": len(result.warnings),
            "rows": int(len(result.df)),
            "compared_with": (result.baseline or {}).get("learned_from") or None,
        }
        with self.lock:
            self._write_history(self.history() + [entry])

    # -- checking ---------------------------------------------------------
    def _serialize(self, result_id: str) -> Dict:
        held = self._held(result_id)
        result: CheckResult = held["result"]
        payload = result.to_dict()
        payload.update(
            id=result_id,
            dataset=held["dataset"],
            seconds=held["seconds"],
            hidden=result.hidden,
            sample=held.get("sample", False),
            findings=[
                dict(
                    f.to_dict(),
                    index=i,
                    key=f.key,
                    category=CATEGORIES.get(f.code, "Finding"),
                    has_rows=f.rows is not None and len(f.rows) > 0,
                )
                for i, f in enumerate(result.findings)
            ],
        )
        return payload

    def _held(self, result_id: str) -> Dict:
        held = self.results.get(result_id or "")
        if held is None:
            raise NotFound("That result is no longer in memory. Check the file again.")
        return held

    def _run(self, df: pd.DataFrame, filename: str, sample: bool = False) -> Dict:
        started = time.perf_counter()
        found = None if sample else base.find_baseline(filename, df.columns, folder=self.store)
        known = None
        if found:
            try:
                known = base.load(found)
            except Exception as error:
                raise DataFileError(
                    f"The saved description of this dataset ({found}) is damaged ({error}). "
                    "Delete it under My datasets and save the file as normal again."
                )
        result = check(df, baseline=known if known else False, name=filename)
        result.baseline_source = found
        dataset = (known or {}).get("name") or base.dataset_name(filename)
        result_id = secrets.token_hex(8)
        with self.lock:
            self.results[result_id] = {
                "result": result,
                "dataset": dataset,
                "seconds": round(time.perf_counter() - started, 2),
                "sample": sample,
            }
            while len(self.results) > RESULTS_KEPT:
                self.results.popitem(last=False)
        if not sample:
            self._remember(result, dataset, result_id)
        return self._serialize(result_id)

    def check_upload(self, filename: str, content: bytes, sheet: Optional[str] = None) -> Dict:
        filename = safe_filename(filename)
        path = os.path.join(self.workdir.name, f"{secrets.token_hex(6)}_{filename}")
        with open(path, "wb") as handle:
            handle.write(content)
        try:
            sheets = excel_sheets(path)
            if len(sheets) > 1 and sheet is None:
                upload_id = secrets.token_hex(8)
                self._drop_pending()
                self.pending[upload_id] = {"path": path, "filename": filename}
                path = None  # kept until a sheet is chosen
                return {"needs_sheet": True, "upload": upload_id, "sheets": sheets, "file": filename}
            return self._run(load_file(path, sheet=sheet), filename)
        finally:
            if path and os.path.exists(path):
                os.remove(path)

    def check_sheet(self, upload_id: str, sheet: str) -> Dict:
        pending = self.pending.get(upload_id or "")
        if pending is None:
            raise NotFound("Choose the file again.")
        try:
            return self._run(load_file(pending["path"], sheet=sheet), pending["filename"])
        finally:
            self._drop_pending()

    def _drop_pending(self) -> None:
        for pending in self.pending.values():
            if os.path.exists(pending["path"]):
                os.remove(pending["path"])
        self.pending.clear()

    def check_sample(self) -> Dict:
        return self._run(sample_frame(), "sample_customers.csv", sample=True)

    # -- rows -------------------------------------------------------------
    def _finding_rows(self, result: CheckResult, finding: str):
        """(rows DataFrame with a reason column first, highlighted column or None, title)"""
        reason = pd.Series(dtype=object)
        if finding in ("", "all", None):
            rows = result.bad_rows()
            reasons = rows.pop("_pdq_reason")
            return rows, reasons, None, "All affected rows"
        try:
            chosen = result.findings[int(finding)]
        except (ValueError, IndexError):
            raise NotFound("That finding is not part of this result.")
        if chosen.rows is None or len(chosen.rows) == 0:
            return result.df.iloc[:0], reason, None, chosen.message
        rows = result.df.loc[result.df.index.isin(chosen.rows)]
        label = chosen.code.replace("_", " ")
        reasons = pd.Series([label] * len(rows), index=rows.index)
        highlight = chosen.column if chosen.column in result.df.columns else None
        return rows, reasons, highlight, chosen.message

    def rows(self, result_id: str, finding: str) -> Dict:
        result: CheckResult = self._held(result_id)["result"]
        rows, reasons, highlight, title = self._finding_rows(result, finding)
        shown = rows.head(ROWS_SHOWN)
        return {
            "title": title,
            "file": result.name,
            "total": int(len(rows)),
            "shown": int(len(shown)),
            "file_rows": int(len(result.df)),
            "columns": [str(c) for c in rows.columns],
            "highlight": str(highlight) if highlight is not None else None,
            "rows": [
                {
                    "row": _cell(index + 2 if isinstance(index, (int, np.integer)) else index),
                    "reason": reasons.loc[index],
                    "cells": [_cell(v) for v in record],
                }
                for index, record in zip(shown.index, shown.itertuples(index=False, name=None))
            ],
            "findings": [
                {"index": i, "message": f.message, "count": int(len(f.rows))}
                for i, f in enumerate(result.findings)
                if f.rows is not None and len(f.rows) > 0
            ],
        }

    def rows_csv(self, result_id: str, finding: str):
        result: CheckResult = self._held(result_id)["result"]
        rows, reasons, _, _ = self._finding_rows(result, finding)
        rows = rows.copy()
        rows.insert(0, "reason", reasons)
        stem = os.path.splitext(safe_filename(result.name))[0]
        return rows.to_csv(index=False), f"{stem}_problem_rows.csv"

    def report(self, result_id: str):
        result: CheckResult = self._held(result_id)["result"]
        stem = os.path.splitext(safe_filename(result.name))[0]
        return report_html(result), f"{stem}_check.html"

    # -- telling the makers -----------------------------------------------
    def feedback(self, result_id: str, finding: str) -> Dict:
        """A false-alarm report for one finding. Built here, shown in full, and sent by nobody but the user."""
        result: CheckResult = self._held(result_id)["result"]
        try:
            chosen = result.findings[int(finding)]
        except (ValueError, IndexError):
            raise NotFound("That finding is not in this result.")
        return {"report": false_alarm_report(result, chosen, CATEGORIES.get(chosen.code, ""))}

    # -- fixing -----------------------------------------------------------
    def fixes(self, result_id: str) -> Dict:
        result: CheckResult = self._held(result_id)["result"]
        proposals = [p.to_dict() for p in result.fixes()]
        return {
            "id": result_id,
            "file": result.name,
            "rows": int(len(result.original)),
            "fixable": [p for p in proposals if p["options"]],
            "not_fixable": [p for p in proposals if not p["options"] and p["level"] != "note"],
        }

    def apply_fixes(self, result_id: str, choices) -> Dict:
        held = self._held(result_id)
        result: CheckResult = held["result"]
        if not isinstance(choices, dict) or not choices:
            raise BadRequest("Choose at least one thing to fix.")
        try:
            outcome = result.fix({str(key): str(action) for key, action in choices.items()})
        except ValueError as error:
            raise BadRequest(str(error))
        held["fixed"] = outcome
        again = outcome.result
        return {
            "id": result_id,
            "file": fixer.fixed_name(safe_filename(result.name)),
            "removed_rows": outcome.removed_rows,
            "changed_cells": outcome.changed_cells,
            "rows_left": int(len(outcome.df)),
            "after": {
                "verdict": again.verdict,
                "headline": again.headline,
                "problems": len(again.problems),
                "warnings": len(again.warnings),
                "left": [f.message for f in again.findings if f.level != NOTE][:8],
            },
        }

    def _fixed(self, result_id: str):
        held = self._held(result_id)
        if "fixed" not in held:
            raise NotFound("No corrected copy has been made for this result yet.")
        return held["result"], held["fixed"]

    def fixed_file(self, result_id: str):
        result, outcome = self._fixed(result_id)
        name = fixer.fixed_name(safe_filename(result.name))
        if name.endswith(".xlsx"):
            buffer = io.BytesIO()
            outcome.df.to_excel(buffer, index=False)
            kind = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            return buffer.getvalue(), name, kind
        return outcome.df.to_csv(index=False), name, "text/csv"

    def fixed_changes(self, result_id: str):
        result, outcome = self._fixed(result_id)
        stem = os.path.splitext(safe_filename(result.name))[0]
        return outcome.changes_frame().to_csv(index=False), f"{stem}_changes.csv"

    # -- baselines --------------------------------------------------------
    def _dataset_path(self, name: str) -> str:
        return os.path.join(self.store, f"{safe_dataset_name(name)}.yml")

    def preview(self, result_id: str) -> Dict:
        held = self._held(result_id)
        result: CheckResult = held["result"]
        learned = base.learn(result.df, sem.infer_kinds(result.df), name=held["dataset"], source=result.name)
        if result.baseline:
            learned["skip"] = list(result.baseline.get("skip") or [])
        return {
            "name": held["dataset"],
            "file": result.name,
            "replaces": bool(result.baseline_source),
            "rows": int(len(result.df)),
            "problems": len(result.problems),
            "warnings": len(result.warnings),
            "columns": describe_baseline(learned),
        }

    def accept(self, result_id: str, name: Optional[str], skip: List[str]) -> Dict:
        held = self._held(result_id)
        if held.get("sample"):
            raise BadRequest("The sample file cannot be saved. Check one of your own files.")
        result: CheckResult = held["result"]
        dataset = safe_dataset_name(name or held["dataset"])
        path = result.baseline_source or self._dataset_path(dataset)
        if not result.baseline_source and os.path.isfile(path):
            # The same name as an existing dataset: keep its rules, replace what is normal
            pass
        learned = base.learn(result.df, sem.infer_kinds(result.df), name=dataset, source=result.name)
        columns = {str(c) for c in result.df.columns}
        learned["skip"] = sorted(str(c) for c in (skip or []) if str(c) in columns)
        base.save(learned, path)
        return {
            "dataset": learned["name"],
            "message": f"Saved. The next {learned['name']} file will be compared with {result.name}.",
        }

    def ignore(self, result_id: str, key: str) -> Dict:
        """Stop reporting one finding for this dataset, then check again."""
        held = self._held(result_id)
        result: CheckResult = held["result"]
        if not result.baseline_source:
            raise BadRequest("Save this file as normal first. Then individual findings can be marked as fine.")
        if key not in {f.key for f in result.findings}:
            raise NotFound("That finding is not part of this result.")
        known = base.load(result.baseline_source)
        ignored = list(known.get("ignore") or [])
        if key not in ignored:
            ignored.append(key)
        known["ignore"] = ignored
        base.save(known, result.baseline_source)

        refreshed = check(result.df, baseline=known, name=result.name)
        refreshed.baseline_source = result.baseline_source
        held["result"] = refreshed
        return self._serialize(result_id)

    def datasets(self) -> List[Dict]:
        history = self.history()
        listed = []
        if not os.path.isdir(self.store):
            return listed
        for filename in sorted(os.listdir(self.store)):
            if not filename.endswith(".yml"):
                continue
            key = filename[:-4]
            entry = {"key": key, "name": key, "damaged": False}
            try:
                known = base.load(os.path.join(self.store, filename))
                entry.update(
                    name=known.get("name") or key,
                    learned_from=known.get("learned_from") or "",
                    learned_on=str(known.get("learned_on") or ""),
                    rows=int(known.get("rows") or 0),
                    columns=len(known.get("columns") or {}),
                )
            except Exception:
                entry["damaged"] = True
            checks = [h for h in history if h.get("dataset") == entry["name"]]
            entry["checks"] = len(checks)
            entry["last"] = checks[-1] if checks else None
            listed.append(entry)
        listed.sort(key=lambda e: (e["last"] or {}).get("when", ""), reverse=True)
        return listed

    def dataset(self, key: str) -> Dict:
        path = self._dataset_path(key)
        if not os.path.isfile(path):
            raise NotFound("That dataset no longer exists.")
        try:
            known = base.load(path)
        except Exception as error:
            raise BadRequest(f"The saved description of this dataset is damaged ({error}). Delete it and save again.")
        name = known.get("name") or key
        rules = known.get("rules") or {}
        return {
            "key": safe_dataset_name(key),
            "name": name,
            "learned_from": known.get("learned_from") or "",
            "learned_on": str(known.get("learned_on") or ""),
            "rows": int(known.get("rows") or 0),
            "path": path,
            "columns": describe_baseline(known),
            "rules": [
                {"column": str(column), "rule": str(rule)}
                for column, listed in rules.items()
                for rule in ([listed] if isinstance(listed, str) else listed or [])
            ],
            "ignored": [str(k) for k in (known.get("ignore") or [])],
            "history": [h for h in self.history() if h.get("dataset") == name][::-1],
        }

    def unignore(self, key: str, finding_key: str) -> Dict:
        path = self._dataset_path(key)
        if not os.path.isfile(path):
            raise NotFound("That dataset no longer exists.")
        known = base.load(path)
        known["ignore"] = [k for k in (known.get("ignore") or []) if k != finding_key]
        base.save(known, path)
        return self.dataset(key)

    def delete_dataset(self, key: str) -> Dict:
        path = self._dataset_path(key)
        if not os.path.isfile(path):
            raise NotFound("That dataset no longer exists.")
        try:
            name = base.load(path).get("name") or key
        except Exception:
            name = key
        os.remove(path)
        with self.lock:
            self._write_history([h for h in self.history() if h.get("dataset") != name])
        return {"deleted": name}

    def state(self) -> Dict:
        from . import __version__

        recent = self.history()[::-1][:8]
        for entry in recent:
            entry["open"] = entry.get("id") in self.results
        return {
            "version": __version__,
            "home": self.home,
            "recent": recent,
            "datasets": len(self.datasets()),
            "max_mb": MAX_UPLOAD_BYTES // (1024 * 1024),
        }

    def forget_everything(self) -> Dict:
        """Delete every saved baseline and the check history."""
        removed = 0
        if os.path.isdir(self.store):
            for filename in os.listdir(self.store):
                if filename.endswith(".yml"):
                    os.remove(os.path.join(self.store, filename))
                    removed += 1
        if os.path.isfile(self.history_path):
            os.remove(self.history_path)
        return {"removed": removed}


MISSING_BUILD = (
    "<!doctype html><meta charset='utf-8'><title>PyDataQuality</title>"
    "<body style='font:16px system-ui;max-width:40rem;margin:4rem auto;padding:0 1rem'>"
    "<h1>The app files are missing</h1><p>This copy of PyDataQuality was installed without its "
    "browser app. Reinstall with <code>pip install --force-reinstall pydataquality</code>, or if you "
    "are working from the source code run <code>npm install</code> and <code>npm run build</code> "
    "in the <code>frontend</code> folder.</p><p><code>pdq check yourfile.csv</code> works without it.</p>"
)


def _make_handler(app: App):
    class Handler(BaseHTTPRequestHandler):
        server_version = "pdq"

        def log_message(self, *args):  # keep the terminal quiet
            pass

        # -- helpers ------------------------------------------------------
        def _send(self, status, body, content_type="application/json", headers=None):
            payload = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(status)
            if content_type.startswith("text/") or content_type in ("application/json", "application/javascript"):
                content_type += "; charset=utf-8"
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            for key, value in dict({"Cache-Control": "no-store"}, **(headers or {})).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, status, data):
            self._send(status, json.dumps(data, default=str))

        def _local(self) -> bool:
            host = (self.headers.get("Host") or "").split(":")[0]
            return host in ("127.0.0.1", "localhost")

        def _query(self):
            parsed = urlparse(self.path)
            return parsed.path, {k: v[0] for k, v in parse_qs(parsed.query).items()}

        def _authorised(self, query) -> bool:
            supplied = self.headers.get("X-PDQ-Token") or query.get("t", "")
            return secrets.compare_digest(supplied, app.token)

        def _body(self, limit) -> bytes:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            if length > limit:
                raise BadRequest("too_large")
            return self.rfile.read(length) if length > 0 else b""

        def _json_body(self) -> Dict:
            raw = self._body(MAX_JSON_BYTES)
            if not raw:
                return {}
            try:
                data = json.loads(raw.decode("utf-8"))
            except ValueError:
                raise BadRequest("The request could not be understood.")
            if not isinstance(data, dict):
                raise BadRequest("The request could not be understood.")
            return data

        def _static(self, path: str):
            if path in ("/", "/index.html"):
                index = os.path.join(STATIC, "index.html")
                if not os.path.isfile(index):
                    return self._send(200, MISSING_BUILD, "text/html")
                with open(index, "r", encoding="utf-8") as handle:
                    page = handle.read().replace(TOKEN_PLACEHOLDER, app.token)
                policy = (
                    "default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; "
                    "connect-src 'self'; font-src 'self'; object-src 'none'; base-uri 'none'; "
                    "form-action 'none'; frame-ancestors 'none'"
                )
                return self._send(200, page, "text/html", {"Content-Security-Policy": policy})
            target = os.path.realpath(os.path.join(STATIC, unquote(path).lstrip("/")))
            root = os.path.realpath(STATIC)
            if not target.startswith(root + os.sep) or not os.path.isfile(target):
                return self._json(404, {"error": "Not found."})
            kind = mimetypes.guess_type(target)[0] or "application/octet-stream"
            if target.endswith(".js"):
                kind = "application/javascript"
            with open(target, "rb") as handle:
                return self._send(200, handle.read(), kind, {"Cache-Control": "max-age=31536000, immutable"})

        def _guarded(self, work):
            try:
                return work()
            except NotFound as error:
                return self._json(404, {"error": str(error)})
            except BadRequest as error:
                return self._json(400, {"error": str(error)})
            except DataFileError as error:
                return self._json(400, {"error": str(error)})
            except Exception as error:  # never leave the page hanging on a crash
                return self._json(500, {"error": f"Something went wrong inside PyDataQuality: {error}"})

        # -- routes -------------------------------------------------------
        def do_GET(self):
            if not self._local():
                return self._json(403, {"error": "This page only answers on this computer."})
            path, query = self._query()
            if not path.startswith(("/api/", "/download/")):
                return self._static(path)
            if not self._authorised(query):
                return self._json(403, {"error": "Open the page from the pdq window and try again."})

            def work():
                if path == "/api/state":
                    return self._json(200, app.state())
                if path == "/api/result":
                    return self._json(200, app._serialize(query.get("id", "")))
                if path == "/api/rows":
                    return self._json(200, app.rows(query.get("id", ""), query.get("finding", "all")))
                if path == "/api/preview":
                    return self._json(200, app.preview(query.get("id", "")))
                if path == "/api/datasets":
                    return self._json(200, {"datasets": app.datasets()})
                if path == "/api/dataset":
                    return self._json(200, app.dataset(query.get("key", "")))
                if path == "/download/rows":
                    body, name = app.rows_csv(query.get("id", ""), query.get("finding", "all"))
                    return self._send(200, body, "text/csv", {"Content-Disposition": f'attachment; filename="{name}"'})
                if path == "/api/feedback":
                    return self._json(200, app.feedback(query.get("id", ""), query.get("finding", "")))
                if path == "/api/fixes":
                    return self._json(200, app.fixes(query.get("id", "")))
                if path == "/download/fixed":
                    body, name, kind = app.fixed_file(query.get("id", ""))
                    return self._send(200, body, kind, {"Content-Disposition": f'attachment; filename="{name}"'})
                if path == "/download/changes":
                    body, name = app.fixed_changes(query.get("id", ""))
                    return self._send(200, body, "text/csv", {"Content-Disposition": f'attachment; filename="{name}"'})
                if path == "/download/report":
                    body, name = app.report(query.get("id", ""))
                    return self._send(200, body, "text/html", {"Content-Disposition": f'attachment; filename="{name}"'})
                raise NotFound("Not found.")

            return self._guarded(work)

        def do_POST(self):
            path, query = self._query()
            if not self._local() or not self._authorised({}):
                return self._json(403, {"error": "Open the page from the pdq window and try again."})

            def work():
                if path == "/api/check":
                    try:
                        content = self._body(MAX_UPLOAD_BYTES)
                    except BadRequest:
                        return self._json(
                            413,
                            {"error": "This file is larger than 300 MB. Use the pdq check command for big files."},
                        )
                    if not content:
                        raise BadRequest("The file is empty.")
                    return self._json(200, app.check_upload(query.get("name", "data.csv"), content, query.get("sheet")))
                body = self._json_body()
                if path == "/api/check-sheet":
                    return self._json(200, app.check_sheet(body.get("upload"), str(body.get("sheet", ""))))
                if path == "/api/sample":
                    return self._json(200, app.check_sample())
                if path == "/api/accept":
                    return self._json(200, app.accept(body.get("id"), body.get("name"), body.get("skip") or []))
                if path == "/api/fix":
                    return self._json(200, app.apply_fixes(body.get("id"), body.get("choices")))
                if path == "/api/ignore":
                    return self._json(200, app.ignore(body.get("id"), str(body.get("key", ""))))
                if path == "/api/unignore":
                    return self._json(200, app.unignore(str(body.get("dataset", "")), str(body.get("key", ""))))
                if path == "/api/delete-dataset":
                    return self._json(200, app.delete_dataset(str(body.get("dataset", ""))))
                if path == "/api/forget-everything":
                    return self._json(200, app.forget_everything())
                raise NotFound("Not found.")

            return self._guarded(work)

    return Handler


def make_server(port: int = 0, home: str = HOME):
    """Build the local server without starting it. Returns (server, app)."""
    app = App(home=home)
    server = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(app))
    return server, app


def serve(port: int = 0, open_browser: bool = True, out=None) -> None:
    """Run the app until interrupted."""
    import sys

    out = out or sys.stdout
    server, app = make_server(port)
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    print(f"PyDataQuality is running at {url}", file=out)
    print("Drop a file on the page to check it. Files stay on this computer.", file=out)
    print("Press Ctrl+C here to stop.", file=out)
    if open_browser:
        threading.Timer(0.4, webbrowser.open, args=(url,)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        app.close()
        print("\nStopped.", file=out)
