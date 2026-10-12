"""
The check result as a web page.

``report_html`` turns a result into one self-contained HTML file to send to
whoever produced the data. ``serve`` runs a small page on this computer where a
file can be dropped in and checked without using the command line.

The server listens on 127.0.0.1 only and nothing is sent anywhere else.
"""

import html
import json
import os
import re
import secrets
import tempfile
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Dict, Optional
from urllib.parse import parse_qs, urlparse

from . import baseline as base
from . import semantic as sem
from .checker import CheckResult, DataFileError, check, load_file

MAX_UPLOAD_BYTES = 300 * 1024 * 1024
STORE = os.path.join(os.path.expanduser("~"), ".pydataquality", "baselines")

CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#141821;--ink2:#566074;--line:#dfe3ea;--accent:#1f4fbf;
--bad:#b42318;--bad-bg:#fdecea;--warn:#8a5300;--warn-bg:#fdf3dc;--good:#0f7a3d;--good-bg:#e3f5ea}
@media (prefers-color-scheme:dark){:root{--bg:#0f1218;--card:#181c25;--ink:#eef1f6;--ink2:#aab2c2;
--line:#2b3140;--accent:#8fb2ff;--bad:#ff9b92;--bad-bg:#3a1a18;--warn:#f0c060;--warn-bg:#35280e;
--good:#6fdc9a;--good-bg:#12301f}}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.55 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}
main{max-width:46rem;margin:0 auto;padding:32px 20px 64px}
h1{font-size:1.5rem;margin:0 0 4px}
.sub{color:var(--ink2);margin:0 0 24px}
.verdict{border-radius:12px;padding:18px 20px;margin:0 0 8px;border:1px solid transparent}
.verdict b{display:block;font-size:1.45rem;letter-spacing:.01em}
.verdict span{color:var(--ink2)}
.verdict.problems{background:var(--bad-bg);border-color:var(--bad)}.verdict.problems b{color:var(--bad)}
.verdict.warnings{background:var(--warn-bg);border-color:var(--warn)}.verdict.warnings b{color:var(--warn)}
.verdict.ok{background:var(--good-bg);border-color:var(--good)}.verdict.ok b{color:var(--good)}
.meta{color:var(--ink2);font-size:.92rem;margin:0 0 20px}
h2{font-size:.78rem;letter-spacing:.09em;text-transform:uppercase;margin:26px 0 8px}
h2.problem{color:var(--bad)}h2.warning{color:var(--warn)}h2.note,h2.clean{color:var(--ink2)}
ol.findings{list-style:none;margin:0;padding:0;display:grid;gap:8px}
ol.findings li{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px}
ol.findings small{display:block;color:var(--ink2);margin-top:4px}
.clean-list{color:var(--ink2);margin:0}
.actions{display:flex;flex-wrap:wrap;gap:10px;margin:24px 0 0}
button,a.button{font:inherit;padding:10px 16px;border-radius:8px;border:1px solid var(--line);background:var(--card);
color:var(--ink);cursor:pointer;text-decoration:none}
button.primary{background:var(--accent);border-color:var(--accent);color:#fff}
@media (prefers-color-scheme:dark){button.primary{color:#0f1218}}
button:focus-visible,a.button:focus-visible,#drop:focus-visible{outline:3px solid var(--accent);outline-offset:2px}
#drop{border:2px dashed var(--line);border-radius:14px;background:var(--card);padding:44px 20px;text-align:center;cursor:pointer}
#drop.over{border-color:var(--accent)}
#drop strong{display:block;font-size:1.15rem;margin-bottom:4px}
#drop span{color:var(--ink2)}
.private{color:var(--ink2);font-size:.9rem;margin:14px 0 24px}
.message{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 14px;margin:16px 0}
footer{color:var(--ink2);font-size:.85rem;margin-top:36px}
"""

TITLES = {"problem": "Problems", "warning": "Warnings", "note": "Also noted"}


def _e(value) -> str:
    return html.escape(str(value), quote=True)


def result_fragment(result: CheckResult, explain: bool = True) -> str:
    """The verdict and findings as an HTML fragment (no <html> wrapper)."""
    counts = []
    if result.problems:
        counts.append(f"{len(result.problems)} problem{'s' if len(result.problems) != 1 else ''}")
    if result.warnings:
        counts.append(f"{len(result.warnings)} warning{'s' if len(result.warnings) != 1 else ''}")
    if result.has_baseline:
        source = result.baseline.get("learned_from") or result.baseline.get("name") or "the saved baseline"
        compared = f"Compared with {_e(source)}."
    else:
        compared = "No earlier file to compare with, so this only covers what is wrong in any file."

    parts = [
        f'<div class="verdict {result.verdict}"><b>{_e(result.headline.capitalize())}</b>'
        f'<span>{_e(", ".join(counts)) if counts else "No findings."}</span></div>',
        f'<p class="meta">{_e(result.name)}: {len(result.df):,} rows, {len(result.df.columns):,} columns. {compared}</p>',
    ]
    for level, group in (("problem", result.problems), ("warning", result.warnings), ("note", result.notes)):
        if not group:
            continue
        parts.append(f'<h2 class="{level}">{TITLES[level]}</h2><ol class="findings">')
        for finding in group:
            why = f"<small>{_e(finding.why)}</small>" if explain and finding.why else ""
            parts.append(f"<li>{_e(finding.message)}{why}</li>")
        parts.append("</ol>")

    clean = result.clean_columns()
    if clean and result.findings:
        label = "Unchanged" if result.has_baseline else "No issues in"
        parts.append(f'<h2 class="clean">{label}</h2><p class="clean-list">{_e(", ".join(clean))}</p>')
    return "\n".join(parts)


def _page(title: str, body: str, script: str = "") -> str:
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{_e(title)}</title><style>{CSS}</style></head><body><main>{body}</main>"
        f"{'<script>' + script + '</script>' if script else ''}</body></html>"
    )


def report_html(result: CheckResult) -> str:
    """One self-contained page summarising a check, to share with the sender of the file."""
    import datetime

    body = (
        f"<h1>Data file check</h1><p class=\"sub\">{_e(result.name)}</p>"
        + result_fragment(result)
        + f"<footer>Checked on {datetime.date.today().isoformat()} with PyDataQuality. "
        "The check ran on the recipient's computer.</footer>"
    )
    return _page(f"Check: {result.name}", body)


# --------------------------------------------------------------------------
# Local drag-and-drop page
# --------------------------------------------------------------------------
UI_BODY = """
<h1>Is this file safe to use?</h1>
<p class="sub">Drop in a spreadsheet or CSV. You get a plain answer in a few seconds.</p>
<div id="drop" tabindex="0" role="button" aria-label="Choose a file to check">
  <strong>Drop a file here</strong><span>or click to choose one. CSV, Excel, JSON or Parquet.</span>
  <input id="file" type="file" hidden accept=".csv,.tsv,.txt,.xlsx,.xlsm,.xls,.json,.parquet">
</div>
<p class="private">The file stays on this computer. Nothing is uploaded to the internet.</p>
<div id="status" class="message" hidden></div>
<div id="result"></div>
<div id="actions" class="actions" hidden>
  <a id="rows" class="button" href="#">Download the affected rows</a>
  <a id="report" class="button" href="#">Download a summary to share</a>
  <button id="accept" class="primary" type="button">This file is fine. Remember it as normal</button>
</div>
"""

UI_SCRIPT = """
const TOKEN = %(token)s;
const drop = document.getElementById('drop'), input = document.getElementById('file');
const statusBox = document.getElementById('status'), resultBox = document.getElementById('result');
const actions = document.getElementById('actions');
let current = null;

function say(text) { statusBox.textContent = text; statusBox.hidden = !text; }

async function send(file) {
  say('Checking ' + file.name + '...');
  resultBox.innerHTML = ''; actions.hidden = true;
  try {
    const response = await fetch('/check?name=' + encodeURIComponent(file.name),
      { method: 'POST', headers: { 'X-PDQ-Token': TOKEN }, body: file });
    const data = await response.json();
    if (!response.ok) { say(data.error); return; }
    say('');
    current = data.id;
    resultBox.innerHTML = data.html;
    actions.hidden = false;
    const query = '?id=' + data.id + '&t=' + TOKEN;
    document.getElementById('rows').href = '/rows' + query;
    document.getElementById('rows').hidden = data.affected_rows === 0;
    document.getElementById('report').href = '/report' + query;
    document.getElementById('accept').textContent = data.has_baseline
      ? 'These changes are fine. Make this the new normal'
      : 'This file is fine. Remember it as normal';
  } catch (error) {
    say('The check could not run. Is the pdq window still open?');
  }
}

document.getElementById('accept').addEventListener('click', async () => {
  const response = await fetch('/accept?id=' + current, { method: 'POST', headers: { 'X-PDQ-Token': TOKEN } });
  const data = await response.json();
  say(response.ok ? data.message : data.error);
});
drop.addEventListener('click', () => input.click());
drop.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); input.click(); } });
input.addEventListener('change', () => { if (input.files[0]) send(input.files[0]); input.value = ''; });
['dragenter', 'dragover'].forEach(n => drop.addEventListener(n, e => { e.preventDefault(); drop.classList.add('over'); }));
['dragleave', 'drop'].forEach(n => drop.addEventListener(n, e => { e.preventDefault(); drop.classList.remove('over'); }));
drop.addEventListener('drop', e => { if (e.dataTransfer.files[0]) send(e.dataTransfer.files[0]); });
"""


def _safe_filename(name: str) -> str:
    name = os.path.basename(name.replace("\\", "/")) or "data.csv"
    return re.sub(r"[^A-Za-z0-9._ ()-]", "_", name)[:120]


class _App:
    """State shared by the request handlers of one running page."""

    def __init__(self, store: str = STORE):
        self.token = secrets.token_urlsafe(24)
        self.store = store
        self.workdir = tempfile.TemporaryDirectory(prefix="pdq_")
        self.results: Dict[str, CheckResult] = {}
        self.lock = threading.Lock()

    def check_upload(self, filename: str, content: bytes) -> Dict:
        filename = _safe_filename(filename)
        path = os.path.join(self.workdir.name, filename)
        with open(path, "wb") as handle:
            handle.write(content)
        try:
            df = load_file(path)
        finally:
            os.remove(path)

        found = base.find_baseline(filename, df.columns, folder=self.store)
        result = check(df, baseline=base.load(found) if found else False, name=filename)
        result.baseline_source = found
        result_id = secrets.token_hex(8)
        with self.lock:
            self.results = {result_id: result}  # only the latest file is kept in memory
        return {
            "id": result_id,
            "html": result_fragment(result),
            "verdict": result.verdict,
            "has_baseline": result.has_baseline,
            "affected_rows": int(len(result.bad_rows())),
        }

    def accept(self, result_id: str) -> str:
        result = self.results[result_id]
        path = result.baseline_source or base.baseline_path(result.name, folder=self.store)
        name = os.path.splitext(os.path.basename(path))[0]
        learned = base.learn(result.df, sem.infer_kinds(result.df), name=name, source=result.name)
        base.save(learned, path)
        return f"Saved. The next file like {result.name} will be compared with this one. Baseline: {path}"


def _make_handler(app: _App):
    class Handler(BaseHTTPRequestHandler):
        server_version = "pdq"

        def log_message(self, *args):  # keep the terminal quiet
            pass

        # -- helpers ------------------------------------------------------
        def _send(self, status, body, content_type="application/json", headers=None):
            payload = body if isinstance(body, bytes) else body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", f"{content_type}; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for key, value in (headers or {}).items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(payload)

        def _json(self, status, data):
            self._send(status, json.dumps(data))

        def _local(self) -> bool:
            # Refuse requests addressed to any other host name (DNS rebinding)
            host = (self.headers.get("Host") or "").split(":")[0]
            return host in ("127.0.0.1", "localhost")

        def _query(self):
            parsed = urlparse(self.path)
            return parsed.path, {k: v[0] for k, v in parse_qs(parsed.query).items()}

        def _result(self, query) -> Optional[CheckResult]:
            return app.results.get(query.get("id", ""))

        # -- routes -------------------------------------------------------
        def do_GET(self):
            if not self._local():
                return self._json(403, {"error": "This page only answers on this computer."})
            path, query = self._query()
            if path == "/":
                script = UI_SCRIPT % {"token": json.dumps(app.token)}
                return self._send(200, _page("Check a data file", UI_BODY, script), "text/html")
            if path in ("/rows", "/report"):
                if not secrets.compare_digest(query.get("t", ""), app.token):
                    return self._json(403, {"error": "Open the page from the pdq window and try again."})
                result = self._result(query)
                if result is None:
                    return self._json(404, {"error": "Check the file again first."})
                stem = os.path.splitext(_safe_filename(result.name))[0]
                if path == "/rows":
                    body = result.bad_rows().to_csv(index=False)
                    name, kind = f"{stem}_problem_rows.csv", "text/csv"
                else:
                    body, name, kind = report_html(result), f"{stem}_check.html", "text/html"
                return self._send(200, body, kind, {"Content-Disposition": f'attachment; filename="{name}"'})
            return self._json(404, {"error": "Not found."})

        def do_POST(self):
            if not self._local() or not secrets.compare_digest(
                self.headers.get("X-PDQ-Token", ""), app.token
            ):
                return self._json(403, {"error": "Open the page from the pdq window and try again."})
            path, query = self._query()
            if path == "/check":
                try:
                    length = int(self.headers.get("Content-Length") or 0)
                except ValueError:
                    length = 0
                if length <= 0:
                    return self._json(400, {"error": "The file is empty."})
                if length > MAX_UPLOAD_BYTES:
                    return self._json(413, {"error": "The file is larger than 300 MB. Use the pdq command for big files."})
                content = self.rfile.read(length)
                try:
                    return self._json(200, app.check_upload(query.get("name", "data.csv"), content))
                except DataFileError as error:
                    return self._json(400, {"error": str(error)})
                except Exception as error:
                    return self._json(500, {"error": f"The check failed: {error}"})
            if path == "/accept":
                if self._result(query) is None:
                    return self._json(404, {"error": "Check the file again first."})
                return self._json(200, {"message": app.accept(query["id"])})
            return self._json(404, {"error": "Not found."})

    return Handler


def make_server(port: int = 0, store: str = STORE):
    """Build the local server without starting it. Returns (server, app)."""
    app = _App(store=store)
    server = ThreadingHTTPServer(("127.0.0.1", port), _make_handler(app))
    return server, app


def serve(port: int = 0, open_browser: bool = True, out=None) -> None:
    """Run the drag-and-drop page until interrupted."""
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
        app.workdir.cleanup()
        print("\nStopped.", file=out)
