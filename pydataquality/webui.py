"""
The check result as a single HTML page.

``report_html`` turns a result into one self-contained file to send to whoever
produced the data. It is also what a result shows in a notebook. The page has
no scripts and loads nothing from the internet. The interactive app behind
``pdq ui`` lives in ``server.py``.
"""

import html

from .checker import CheckResult

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
