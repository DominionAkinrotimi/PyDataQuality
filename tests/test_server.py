"""Tests for the local app behind ``pdq ui``: the JSON API and its safety rules."""

import io
import json
import os
import threading
import urllib.error
import urllib.request

import numpy as np
import pandas as pd
import pytest

from pydataquality import server


def people(n=200, seed=0, start=0):
    rng = np.random.default_rng(seed)
    return pd.DataFrame(
        {
            "person_id": np.arange(start, start + n),
            "age": rng.integers(18, 70, n),
            "city": rng.choice(["Lagos", "Accra", "Nairobi"], n),
        }
    )


def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")


@pytest.fixture
def ui(tmp_path):
    http, app = server.make_server(port=0, home=str(tmp_path / "home"))
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{http.server_address[1]}", app
    http.shutdown()
    http.server_close()
    app.close()


def call(url, data=None, headers=None):
    request = urllib.request.Request(url, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, response.read(), dict(response.headers)
    except urllib.error.HTTPError as error:
        return error.code, error.read(), dict(error.headers)


def get(base_url, app, path):
    status, body, _ = call(base_url + path, headers={"X-PDQ-Token": app.token})
    return status, json.loads(body)


def post(base_url, app, path, payload=None):
    status, body, _ = call(
        base_url + path,
        data=json.dumps(payload or {}).encode("utf-8"),
        headers={"X-PDQ-Token": app.token, "Content-Type": "application/json"},
    )
    return status, json.loads(body)


def upload(base_url, app, name, content):
    status, body, _ = call(f"{base_url}/api/check?name={name}", data=content, headers={"X-PDQ-Token": app.token})
    return status, json.loads(body)


# ------------------------------------------------------------------- page
def test_page_is_served_with_the_session_token(ui):
    base_url, app = ui
    status, body, headers = call(base_url + "/")
    assert status == 200
    page = body.decode("utf-8")
    assert app.token in page and server.TOKEN_PLACEHOLDER not in page
    assert "default-src 'self'" in headers["Content-Security-Policy"]


def test_built_app_loads_nothing_from_the_internet():
    index = os.path.join(server.STATIC, "index.html")
    assert os.path.isfile(index), "run `npm run build` in frontend/"
    with open(index, encoding="utf-8") as handle:
        assert "http://" not in handle.read().replace("http://www.w3.org", "")
    assets = os.path.join(server.STATIC, "assets")
    for name in os.listdir(assets):
        if name.endswith(".css"):
            with open(os.path.join(assets, name), encoding="utf-8") as handle:
                assert "fonts.googleapis" not in handle.read()


def test_static_files_cannot_escape_the_app_folder(ui):
    base_url, _ = ui
    for path in ("/../server.py", "/assets/../../server.py", "/%2e%2e/%2e%2e/setup.py"):
        status, body, _ = call(base_url + path)
        assert status == 404 and b"import" not in body


# ------------------------------------------------------------------ checks
def test_sample_check_finds_planted_problems_and_is_not_recorded(ui):
    base_url, app = ui
    status, result = post(base_url, app, "/api/sample")
    assert status == 200 and result["sample"] is True
    assert result["verdict"] == "problems"
    codes = {f["code"] for f in result["findings"]}
    assert {"duplicates", "future_date", "impossible", "spelling", "bad_email", "mixed_dates", "extreme"} <= codes
    assert all(f["category"] for f in result["findings"])
    assert get(base_url, app, "/api/state")[1]["recent"] == []

    status, refused = post(base_url, app, "/api/accept", {"id": result["id"], "name": "sample"})
    assert status == 400 and "sample" in refused["error"]


def test_full_flow_save_compare_rows_ignore(ui):
    base_url, app = ui

    status, first = upload(base_url, app, "people_september.csv", csv_bytes(people(seed=1)))
    assert status == 200 and first["verdict"] == "ok" and not first["has_baseline"]
    assert first["dataset"] == "people"

    status, preview = get(base_url, app, f"/api/preview?id={first['id']}")
    assert status == 200 and [c["name"] for c in preview["columns"]] == ["person_id", "age", "city"]
    assert "3 values" in preview["columns"][2]["holds"]

    status, saved = post(base_url, app, "/api/accept", {"id": first["id"], "name": "People", "skip": ["age"]})
    assert status == 200 and saved["dataset"] == "people"

    changed = people(seed=2, start=500)
    changed.loc[:9, "city"] = "Kumasi"
    changed.loc[:20, "age"] = 5000  # age was unticked, so this must not be compared
    status, second = upload(base_url, app, "people_october.csv", csv_bytes(changed))
    assert status == 200 and second["has_baseline"] and second["compared_with"] == "people_september.csv"
    by_code = {f["code"]: f for f in second["findings"]}
    assert "new_values" in by_code and "out_of_range" not in by_code

    finding = by_code["new_values"]
    status, rows = get(base_url, app, f"/api/rows?id={second['id']}&finding={finding['index']}")
    assert status == 200 and rows["total"] == 10 and rows["highlight"] == "city"
    assert rows["rows"][0]["row"] == "2" and "Kumasi" in rows["rows"][0]["cells"]

    status, body, headers = call(f"{base_url}/download/rows?id={second['id']}&finding=all&t={app.token}")
    assert status == 200 and "attachment" in headers["Content-Disposition"]
    assert "reason" in pd.read_csv(io.BytesIO(body)).columns

    status, body, _ = call(f"{base_url}/download/report?id={second['id']}&t={app.token}")
    assert status == 200 and body.startswith(b"<!doctype html>")

    status, after = post(base_url, app, "/api/ignore", {"id": second["id"], "key": finding["key"]})
    assert status == 200 and after["hidden"] == 1
    assert "new_values" not in {f["code"] for f in after["findings"]}

    status, listed = get(base_url, app, "/api/datasets")
    assert [d["name"] for d in listed["datasets"]] == ["people"] and listed["datasets"][0]["checks"] == 2

    status, detail = get(base_url, app, "/api/dataset?key=people")
    assert detail["ignored"] == [finding["key"]] and len(detail["history"]) == 2
    assert [c["checked"] for c in detail["columns"]] == [True, False, True]

    status, detail = post(base_url, app, "/api/unignore", {"dataset": "people", "key": finding["key"]})
    assert detail["ignored"] == []

    status, _ = post(base_url, app, "/api/delete-dataset", {"dataset": "people"})
    assert status == 200 and get(base_url, app, "/api/datasets")[1]["datasets"] == []


def test_ignoring_needs_a_saved_dataset(ui):
    base_url, app = ui
    df = people()
    df.loc[0, "age"] = 999
    _, result = upload(base_url, app, "people.csv", csv_bytes(df))
    status, refused = post(base_url, app, "/api/ignore", {"id": result["id"], "key": result["findings"][0]["key"]})
    assert status == 400 and "Save this file as normal first" in refused["error"]


def test_workbook_with_several_sheets_asks_which_one(ui, tmp_path):
    pytest.importorskip("openpyxl")
    base_url, app = ui
    path = tmp_path / "book.xlsx"
    with pd.ExcelWriter(path) as writer:
        people(n=30).to_excel(writer, sheet_name="People", index=False)
        pd.DataFrame({"note": ["a", "b"]}).to_excel(writer, sheet_name="Notes", index=False)

    status, choice = upload(base_url, app, "book.xlsx", path.read_bytes())
    assert status == 200 and choice["needs_sheet"] and choice["sheets"] == ["People", "Notes"]

    status, result = post(base_url, app, "/api/check-sheet", {"upload": choice["upload"], "sheet": "Notes"})
    assert status == 200 and result["columns"] == 1 and result["rows"] == 2
    assert os.listdir(app.workdir.name) == []  # the upload is removed once it has been read


def test_history_survives_a_damaged_line_and_can_be_cleared(ui):
    base_url, app = ui
    upload(base_url, app, "people.csv", csv_bytes(people()))
    with open(app.history_path, "a", encoding="utf-8") as handle:
        handle.write("{not json\n")
    status, state = get(base_url, app, "/api/state")
    assert status == 200 and len(state["recent"]) == 1 and state["recent"][0]["open"] is True

    status, done = post(base_url, app, "/api/forget-everything")
    assert status == 200 and get(base_url, app, "/api/state")[1]["recent"] == []


def test_damaged_saved_dataset_gives_a_plain_message(ui):
    base_url, app = ui
    _, first = upload(base_url, app, "people.csv", csv_bytes(people()))
    post(base_url, app, "/api/accept", {"id": first["id"], "name": "people"})
    with open(os.path.join(app.store, "people.yml"), "w", encoding="utf-8") as handle:
        handle.write("columns: [broken")

    status, error = upload(base_url, app, "people.csv", csv_bytes(people(seed=3)))
    assert status == 400 and "damaged" in error["error"]
    listed = get(base_url, app, "/api/datasets")[1]["datasets"]
    assert listed[0]["damaged"] is True
    assert post(base_url, app, "/api/delete-dataset", {"dataset": "people"})[0] == 200


# ------------------------------------------------------------------ safety
def test_requests_without_the_token_are_refused(ui):
    base_url, app = ui
    assert call(f"{base_url}/api/state")[0] == 403
    assert call(f"{base_url}/api/check?name=x.csv", data=csv_bytes(people()))[0] == 403
    assert call(f"{base_url}/api/sample", data=b"{}")[0] == 403
    _, result = upload(base_url, app, "people.csv", csv_bytes(people()))
    assert call(f"{base_url}/download/rows?id={result['id']}&t=wrong")[0] == 403


def test_requests_for_another_host_are_refused(ui):
    base_url, app = ui
    assert call(base_url + "/", headers={"Host": "evil.example"})[0] == 403
    assert call(base_url + "/api/state", headers={"Host": "evil.example", "X-PDQ-Token": app.token})[0] == 403


def test_bad_uploads_get_plain_errors(ui):
    base_url, app = ui
    status, error = upload(base_url, app, "broken.xlsx", b"not a spreadsheet")
    assert status == 400 and "Could not read" in error["error"]
    status, error = upload(base_url, app, "empty.csv", b"")
    assert status == 400 and "empty" in error["error"]
    assert os.listdir(app.workdir.name) == []


def test_unknown_result_and_route(ui):
    base_url, app = ui
    status, error = get(base_url, app, "/api/result?id=nope")
    assert status == 404 and "Check the file again" in error["error"]
    assert get(base_url, app, "/api/nothing")[0] == 404


def test_names_are_made_safe():
    assert server.safe_filename("../../etc/passwd") == "passwd"
    assert server.safe_filename("..\\..\\boot.ini") == "boot.ini"
    assert server.safe_dataset_name("../Sales Export!") == "sales_export"
    assert server.safe_dataset_name("") == "data"
