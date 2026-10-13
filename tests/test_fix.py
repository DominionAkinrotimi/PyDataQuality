"""Tests for fixing a file: what is offered, what is changed, and that the original is left alone."""

import io
import json
import os
import threading
import urllib.request

import pandas as pd
import pytest

import pydataquality as pdq
from pydataquality import fixer, server
from pydataquality.pdq_cli import main as pdq_main


@pytest.fixture
def sample():
    return pdq.check(server.sample_frame(), baseline=False, name="sample_customers.csv")


def options(result, key):
    return {o.action: o for p in result.fixes() if p.key == key for o in p.options}


# ------------------------------------------------------------------ what is offered
def test_only_the_safe_fixes_are_recommended(sample):
    assert fixer.recommended(sample.fixes()) == {
        "duplicates:(whole file)": "remove_rows",
        "spelling:country": "replace",
    }


def test_a_wrong_value_can_be_emptied_or_its_row_removed_but_neither_is_recommended(sample):
    offered = options(sample, "impossible:age")
    assert set(offered) == {"blank", "remove_rows"}
    assert not any(o.recommended for o in offered.values())
    assert offered["blank"].cells == 2 and offered["remove_rows"].rows == 2
    assert offered["blank"].examples[0] == ["999", ""]


def test_spelling_fix_shows_what_becomes_what(sample):
    option = options(sample, "spelling:country")["replace"]
    assert option.cells == 30
    assert ["nigeria ", "Nigeria"] in option.examples and ["NIGERIA", "Nigeria"] in option.examples


def test_whole_file_findings_have_no_fix_and_say_why():
    before = pd.DataFrame({"id": range(100), "city": ["Lagos", "Accra"] * 50, "code": ["a", "b"] * 50})
    known = pdq.baseline.learn(before, pdq.semantic.infer_kinds(before), name="t", source="before.csv")
    result = pdq.check(before.drop(columns=["code"]), baseline=known)
    missing = [p for p in result.fixes() if p.key.startswith("column_missing")][0]
    assert missing.options == []
    assert "whoever produced it" in missing.reason


# ------------------------------------------------------------------ what is changed
def test_default_fix_removes_copies_and_unifies_spelling_and_nothing_else(sample):
    original = sample.original.copy()
    outcome = sample.fix()
    assert outcome.removed_rows == 6 and outcome.changed_cells == 30
    assert len(outcome.df) == len(original) - 6
    assert set(outcome.df["country"].unique()) == {"Nigeria", "Ghana", "Kenya", "South Africa"}
    assert 999 in outcome.df["age"].values  # not chosen, so not touched
    # the result that was fixed still holds the file as it was read
    pd.testing.assert_frame_equal(sample.original, original)
    codes = {f.code for f in outcome.result.findings}
    assert "duplicates" not in codes and "spelling" not in codes
    assert "impossible" in codes


def test_fixing_everything_leaves_a_clean_copy(sample):
    outcome = sample.fix({
        "duplicates:(whole file)": "remove_rows",
        "spelling:country": "replace",
        "impossible:age": "blank",
        "future_date:signup_date": "remove_rows",
        "mixed_dates:signup_date": "reformat",
        "bad_email:email": "blank",
        "extreme:monthly_spend": "blank",
    })
    assert outcome.result.verdict == "ok"
    assert outcome.result.findings == []


def test_every_change_is_listed_with_its_row_and_values(sample):
    outcome = sample.fix({"impossible:age": "blank", "spelling:country": "replace"})
    log = outcome.changes_frame()
    assert list(log.columns) == ["row", "column", "before", "after", "reason"]
    assert len(log) == outcome.changed_cells == 32
    ages = log[log["column"] == "age"]
    assert set(ages["before"]) == {"999", "-4"} and set(ages["after"]) == {""}
    # row numbers are the ones a spreadsheet shows: the first row of data is row 2
    row = int(ages.iloc[0]["row"])
    assert str(sample.original.loc[row - 2, "age"]) == ages.iloc[0]["before"]


def test_removed_rows_are_logged_once_and_not_also_as_cell_changes(sample):
    outcome = sample.fix({"impossible:age": "remove_rows", "spelling:country": "replace"})
    log = outcome.changes_frame()
    removed = log[log["after"] == "removed"]
    assert len(removed) == outcome.removed_rows == 2
    assert not set(removed["row"]) & set(log[log["after"] != "removed"]["row"])


def test_dates_are_rewritten_in_the_main_format(sample):
    outcome = sample.fix({"mixed_dates:signup_date": "reformat"})
    log = outcome.changes_frame()
    assert dict(zip(log["before"], log["after"])) == {"03/04/2025": "2025-04-03", "17/05/2025": "2025-05-17"}
    assert "mixed_dates" not in {f.code for f in outcome.result.findings}


def test_repeated_ids_keep_the_first_of_each():
    df = pd.DataFrame({"order_id": list(range(100)) + [5, 5, 7], "amount": range(103)})
    result = pdq.check(df, baseline=False)
    key = [f.key for f in result.findings if f.code == "id_repeats"][0]
    option = options(result, key)["remove_rows"]
    assert option.rows == 3 and not option.recommended
    outcome = result.fix({key: "remove_rows"})
    assert outcome.df["order_id"].is_unique and len(outcome.df) == 100
    assert list(outcome.df.index[:8]) == list(range(8))  # the first of each stays


def test_dashes_in_the_original_are_not_silently_changed():
    df = pd.DataFrame({
        "ref": range(120),
        "city": ["Lagos", "lagos", "Lagos", "Accra"] * 30,
        "debit": ["10.00", "--", "12.50", "--"] * 30,
    })
    outcome = pdq.check(df, baseline=False).fix()
    assert (outcome.df["debit"] == "--").sum() == 60  # treated as empty when checking, kept as written
    assert set(outcome.df["city"]) == {"Lagos", "Accra"}


def test_unknown_choices_are_refused(sample):
    with pytest.raises(ValueError, match="no finding"):
        sample.fix({"nonsense:column": "blank"})
    with pytest.raises(ValueError, match="not something that can be done"):
        sample.fix({"spelling:country": "remove_rows"})


def test_fixed_name_keeps_excel_as_excel():
    assert fixer.fixed_name("orders.csv") == "orders_fixed.csv"
    assert fixer.fixed_name("Orders March.XLSX") == "Orders March_fixed.xlsx"
    assert fixer.fixed_name("data.json") == "data_fixed.csv"


# ------------------------------------------------------------------ the command
def test_pdq_fix_writes_a_copy_and_a_change_list_and_leaves_the_file_alone(tmp_path):
    path = tmp_path / "customers.csv"
    server.sample_frame().to_csv(path, index=False)
    before = path.read_bytes()
    out = io.StringIO()
    assert pdq_main(["fix", str(path), "--no-baseline", "--apply", "impossible:age=blank"], out=out) == 0
    assert path.read_bytes() == before
    fixed = pd.read_csv(tmp_path / "customers_fixed.csv")
    changes = pd.read_csv(tmp_path / "customers_changes.csv")
    assert len(fixed) == 480
    assert fixed["age"].isna().sum() == 2
    assert len(changes) == 6 + 30 + 2
    text = out.getvalue()
    assert "was not changed" in text and "6 rows removed" in text and "32 cells changed" in text


def test_pdq_fix_list_changes_nothing(tmp_path):
    path = tmp_path / "customers.csv"
    server.sample_frame().to_csv(path, index=False)
    out = io.StringIO()
    assert pdq_main(["fix", str(path), "--no-baseline", "--list"], out=out) == 0
    assert "spelling:country=replace" in out.getvalue() and "done by default" in out.getvalue()
    assert sorted(os.listdir(tmp_path)) == ["customers.csv"]


# ------------------------------------------------------------------ the app
@pytest.fixture
def running(tmp_path):
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
            raw = response.read()
            kind = response.headers.get("Content-Type", "")
            return json.loads(raw) if kind.startswith("application/json") else raw

    yield call, app
    httpd.shutdown()
    httpd.server_close()
    app.close()


def test_app_lists_fixes_applies_them_and_serves_both_files(running):
    call, app = running
    result = call("/api/sample", {})
    listing = call(f"/api/fixes?id={result['id']}")
    assert {p["key"] for p in listing["fixable"]} >= {"duplicates:(whole file)", "spelling:country", "impossible:age"}
    assert listing["rows"] == 486

    outcome = call("/api/fix", {"id": result["id"], "choices": {"duplicates:(whole file)": "remove_rows", "impossible:age": "blank"}})
    assert outcome["removed_rows"] == 6 and outcome["changed_cells"] == 2 and outcome["rows_left"] == 480
    assert outcome["file"] == "sample_customers_fixed.csv"
    assert outcome["after"]["verdict"] == "problems"

    fixed = pd.read_csv(io.BytesIO(call(f"/download/fixed?id={result['id']}&t={app.token}")))
    assert len(fixed) == 480 and fixed["age"].isna().sum() == 2
    changes = pd.read_csv(io.BytesIO(call(f"/download/changes?id={result['id']}&t={app.token}")))
    assert len(changes) == 8


def test_app_refuses_an_empty_choice_and_a_download_before_fixing(running):
    call, app = running
    result = call("/api/sample", {})
    for path, body in ((f"/download/fixed?id={result['id']}&t={app.token}", None), ("/api/fix", {"id": result["id"], "choices": {}})):
        with pytest.raises(urllib.error.HTTPError) as caught:
            call(path, body)
        assert caught.value.code in (400, 404)
