"""
The false-alarm report must hold nothing from inside the file.

People check files of salaries, bank transactions and patient records. The
report is something they may paste into an email or a public issue, so these
tests fill a file with recognisable values and names and check that none of
them, and no column or file name, can be found in any report.
"""

import importlib.util
import json
import os
import threading
import urllib.request

import pandas as pd
import pytest

import pydataquality as pdq
from pydataquality import server
from pydataquality.feedback import false_alarm_report

SECRETS = ["ZEBRA", "zebra", "Quokka", "ocelot@private.example", "9998887776", "2031-07-04", "31/12/2025", "777123.45", "Narwhal"]
COLUMN_NAMES = ["patient_ref", "ward_secret", "salary_ngn", "contact_private", "admitted_on"]


def sensitive_frame():
    n = 240
    frame = pd.DataFrame({
        "patient_ref": [f"9998{i:06d}" for i in range(n)],
        "ward_secret": ["ZEBRA"] * 200 + ["zebra"] * 30 + ["Quokka"] * 10,
        "salary_ngn": [50000.0 + i for i in range(n - 1)] + [777123.45 * 1000],
        "contact_private": [f"person{i}@private.example" for i in range(n - 2)] + ["ocelot@private.example", "Narwhal"],
        "admitted_on": ["2025-03-01"] * (n - 3) + ["2031-07-04", "31/12/2025", "31/12/2025"],
    })
    return pd.concat([frame, frame.iloc[:4]], ignore_index=True)


@pytest.fixture
def result():
    checked = pdq.check(sensitive_frame(), baseline=False, name="Confidential Payroll ACME Hospital.xlsx")
    assert len(checked.findings) >= 4, "the fixture should raise several kinds of finding"
    return checked


def test_no_report_contains_a_value_a_column_name_or_the_file_name(result):
    cells = {str(value) for column in result.original.columns for value in result.original[column].unique()}
    for finding in result.findings:
        report = false_alarm_report(result, finding, "Category")
        for secret in SECRETS + COLUMN_NAMES + ["Confidential", "Payroll", "ACME", "Hospital"]:
            assert secret not in report, f"{secret!r} leaked into the report for {finding.code}"
        # nothing longer than a couple of characters from any cell appears either
        for value in cells:
            if len(value) >= 4:
                assert value not in report, f"a cell value leaked into the report for {finding.code}"
        # the sentence shown on screen quotes values, so it must not be in the report
        assert finding.message not in report
        for example in finding.examples:
            if len(str(example)) >= 3:
                assert str(example) not in report


def test_report_says_what_is_useful(result):
    spelling = [f for f in result.findings if f.code == "spelling"][0]
    report = false_alarm_report(result, spelling, "Spelling")
    assert "Finding: spelling (Spelling)" in report
    assert "About: category" in report
    assert f"Rows affected: {len(spelling.rows)} of 244" in report
    assert "type .xlsx" in report
    assert f"Version: {pdq.__version__}" in report


def test_whole_file_finding_and_unknown_file_type(result):
    duplicates = [f for f in result.findings if f.code == "duplicates"][0]
    assert "About: the whole file" in false_alarm_report(result, duplicates)
    odd = pdq.check(sensitive_frame(), baseline=False, name="DataFrame")
    assert "type not recorded" in false_alarm_report(odd, odd.findings[0])


def test_app_serves_the_report_and_nothing_else(tmp_path):
    httpd, app = server.make_server(0, home=str(tmp_path))
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{httpd.server_address[1]}"

    def call(path, body=None):
        request = urllib.request.Request(
            base + path, data=None if body is None else json.dumps(body).encode(),
            headers={"X-PDQ-Token": app.token, "Content-Type": "application/json"},
            method="GET" if body is None else "POST",
        )
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())

    try:
        checked = call("/api/sample", {})
        answer = call(f"/api/feedback?id={checked['id']}&finding=0")
        assert list(answer) == ["report"]
        assert "Finding: duplicates" in answer["report"]
        assert "sample_customers" not in answer["report"] and "Nigeria" not in answer["report"]
        with pytest.raises(urllib.error.HTTPError) as caught:
            call(f"/api/feedback?id={checked['id']}&finding=99")
        assert caught.value.code == 404
    finally:
        httpd.shutdown()
        httpd.server_close()
        app.close()


# ------------------------------------------------------------------ the daily numbers script
def load_stats_script():
    path = os.path.join(os.path.dirname(__file__), "..", ".github", "scripts", "record_stats.py")
    spec = importlib.util.spec_from_file_location("record_stats", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_recording_twice_in_a_day_keeps_one_row(tmp_path):
    stats = load_stats_script()
    path = str(tmp_path / "daily.csv")
    key = lambda row: row["date"]  # noqa: E731
    stats.upsert(path, ["date", "installer_downloads"], [{"date": "2026-10-12", "installer_downloads": 3}], key)
    stats.upsert(path, ["date", "installer_downloads"], [{"date": "2026-10-13", "installer_downloads": 4}], key)
    rows = stats.upsert(path, ["date", "installer_downloads"], [{"date": "2026-10-13", "installer_downloads": 6}], key)
    assert [(row["date"], str(row["installer_downloads"])) for row in rows] == [("2026-10-12", "3"), ("2026-10-13", "6")]
    assert pd.read_csv(path)["installer_downloads"].tolist() == [3, 6]


def test_numbers_are_sorted_into_platforms_and_traffic_is_skipped_without_a_token(monkeypatch):
    stats = load_stats_script()
    answers = {
        "/releases?per_page=100": [{"tag_name": "v1", "assets": [
            {"name": "PyDataQuality-Setup.exe", "download_count": 5}, {"name": "PyDataQuality-macOS.zip", "download_count": 2},
        ]}],
        "/repos/me/pydataquality": {"stargazers_count": 7},
        "/recent": {"data": {"last_day": 1, "last_week": 9, "last_month": 30}},
    }
    asked = []

    def fake_get(url, token=None):
        asked.append(url)
        for ending, answer in answers.items():
            if url.endswith(ending):
                return answer
        return None

    monkeypatch.setattr(stats, "get", fake_get)
    daily, releases = stats.collect("me/pydataquality", "token", None, "2026-10-13")
    assert (daily["installer_downloads"], daily["windows_downloads"], daily["mac_downloads"]) == (7, 5, 2)
    assert daily["pypi_last_month"] == 30 and daily["stars"] == 7
    assert daily["repo_views_14d"] == ""
    assert not any("traffic" in url for url in asked)
    assert len(releases) == 2
