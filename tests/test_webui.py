"""Tests for the shareable summary page and the local drag-and-drop page."""

import io
import json
import threading
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import pytest

import pydataquality as pdq
from pydataquality import webui
from pydataquality.pdq_cli import main as pdq_main


def people(n=200, seed=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "person_id": np.arange(n),
            "age": rng.integers(18, 70, n),
            "city": rng.choice(["Lagos", "Accra", "Nairobi"], n),
        }
    )


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


# ------------------------------------------------------------------ report
def test_report_is_self_contained_and_escaped():
    df = people()
    df.loc[0, "age"] = 999
    df.loc[1, "city"] = "<script>alert(1)</script>"
    page = pdq.check(df, name="people.csv").to_html()

    assert page.startswith("<!doctype html>")
    assert "Problems found" in page and "999" in page
    assert "<script>alert(1)</script>" not in page
    assert "http://" not in page and "https://" not in page  # no outside resources


def test_notebook_display():
    assert "Nothing obviously wrong" in pdq.check(people())._repr_html_()


def test_cli_report_writes_file(tmp_path):
    data = tmp_path / "people.csv"
    people().to_csv(data, index=False)
    out = io.StringIO()
    assert pdq_main(["report", str(data)], out=out) == 0
    assert (tmp_path / "people_check.html").read_text(encoding="utf-8").startswith("<!doctype html>")


# ---------------------------------------------------------------- local ui
@pytest.fixture
def ui(tmp_path):
    server, app = webui.make_server(port=0, store=str(tmp_path / "baselines"))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}", app
    server.shutdown()
    server.server_close()
    app.workdir.cleanup()


def call(url, data=None, headers=None, method=None):
    request = urllib.request.Request(url, data=data, headers=headers or {}, method=method)
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers)


def post_file(base_url, app, name, df):
    status, body, _ = call(
        f"{base_url}/check?name={name}", data=csv_bytes(df), headers={"X-PDQ-Token": app.token}
    )
    return status, json.loads(body)


def test_page_loads(ui):
    base_url, _ = ui
    status, body, _ = call(base_url + "/")
    assert status == 200 and b"Is this file safe to use?" in body


def test_upload_check_accept_and_compare(ui):
    base_url, app = ui

    status, first = post_file(base_url, app, "people_september.csv", people(seed=1))
    assert status == 200 and first["verdict"] == "ok" and not first["has_baseline"]

    status, body, _ = call(
        f"{base_url}/accept?id={first['id']}", data=b"", headers={"X-PDQ-Token": app.token}
    )
    assert status == 200 and "Saved" in json.loads(body)["message"]

    changed = people(seed=2)
    changed.loc[:9, "city"] = "Kumasi"
    status, second = post_file(base_url, app, "people_october.csv", changed)
    assert status == 200 and second["has_baseline"]
    assert "never seen before" in second["html"] and "Kumasi" in second["html"]

    status, rows, headers = call(f"{base_url}/rows?id={second['id']}&t={app.token}")
    assert status == 200 and "attachment" in headers["Content-Disposition"]
    assert len(pd.read_csv(io.BytesIO(rows))) == 10

    status, page, _ = call(f"{base_url}/report?id={second['id']}&t={app.token}")
    assert status == 200 and page.startswith(b"<!doctype html>")


def test_requests_without_the_token_are_refused(ui):
    base_url, app = ui
    status, _, _ = call(f"{base_url}/check?name=x.csv", data=csv_bytes(people()))
    assert status == 403

    _, first = post_file(base_url, app, "people.csv", people())
    status, _, _ = call(f"{base_url}/rows?id={first['id']}&t=wrong")
    assert status == 403


def test_requests_for_another_host_are_refused(ui):
    base_url, _ = ui
    status, _, _ = call(base_url + "/", headers={"Host": "evil.example"})
    assert status == 403


def test_unreadable_upload_gets_a_plain_error(ui):
    base_url, app = ui
    status, body, _ = call(
        f"{base_url}/check?name=broken.xlsx", data=b"not a spreadsheet", headers={"X-PDQ-Token": app.token}
    )
    assert status == 400 and "Could not read" in json.loads(body)["error"]


def test_upload_name_cannot_escape_the_work_folder():
    assert webui._safe_filename("../../etc/passwd") == "passwd"
    assert webui._safe_filename("..\\..\\boot.ini") == "boot.ini"
